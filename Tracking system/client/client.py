from tkinter import *
from functools import partial
import socket
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import tkinter as tk
import pandas as pd
from datetime import datetime

tab_name = {}  # Define the global dictionary to store tab information
stop_flag = False  # Global flag to control the loop
count = 0  # Global count for received data
client_socket = None  # Global socket object
received_data = {}  # Dictionary to store the received data
num_station_data = 0

# Define the path to the tab data file
tab_data_path = r"tab_data.txt"

def config():
    global tab_name
    tab_name = {}
    try:
        with open(tab_data_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                print(f"Reading line: {line}")  # Debug print
                if line.strip():  # Check if line is not empty
                    line_parts = line.strip().split(':')
                    line_name = line_parts[0].strip()
                    host_port_target = line_parts[1].strip().split()
                    host = host_port_target[0]
                    port = host_port_target[1]
                    target = host_port_target[2] if len(host_port_target) > 2 else '000'  # Set default target if not present
                    tab_name[line_name] = {
                        'HOST': host,
                        'PORT': port,
                        'Target': target
                    }
                    print(f"Parsed line - Name: {line_name}, Host: {host}, Port: {port}, Target: {target}")  # Debug print
    except FileNotFoundError:
        print(f"File {tab_data_path} not found. Starting with an empty configuration.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return tab_name


def write_config():
    global tab_name

    with open(tab_data_path, 'w') as file:
        for key in tab_name:
            file.write(f"{key}: {tab_name[key]['HOST']} {tab_name[key]['PORT']} {tab_name[key]['Target']}\n")
    print("Config updated")


def update_gui(name):
    global received_data, count, num_station_data, total_output_label, total_time_label, graph1, graph2

    time_list = []
    for i in range(0, int(num_station_data)):
        time = 0
        for keys in received_data[name]:
            time += float(received_data[name][keys][i])
        time /= count
        time_list.append(time)

    total_time_list = []
    total_time = 0
    for keys in received_data[name]:
        time = 0
        for i in range(0, int(num_station_data)):
            time += float(received_data[name][keys][i])
        total_time_list.append(time)
        total_time += time

    # Update total output and total time labels
    total_output_label.config(text=str(count))
    total_time_label.config(text=f'{time_list[-1]:.2f}')

    # Clear previous graphs
    for widget in graph1.winfo_children():
        widget.destroy()
    for widget in graph2.winfo_children():
        widget.destroy()

    # Define station names for x-axis labels
    stations = [f'Station {i+1}' for i in range(int(num_station_data))]

    # Plot bar graph in graph1 frame
    fig1 = plt.figure(figsize=(3, 3), facecolor=graph1['bg'])
    ax1 = fig1.add_subplot()
    ax1.set_facecolor(graph1['bg'])
    ax1.bar(stations, time_list, color='#9D1B1B', width=0.5)
    ax1.tick_params(labelsize=7, color="black")
    ax1.set_xlabel('Station')
    ax1.set_ylabel('Average Time')
    ax1.set_title('Average Time at Stations')
    ax1.set_xticks(range(len(stations)))
    ax1.set_xticklabels(stations, rotation=0, ha='right')

    plt.tight_layout()  # Adjust layout to prevent cutting off labels

    canvas1 = FigureCanvasTkAgg(figure=fig1, master=graph1)
    canvas_widget1 = canvas1.get_tk_widget()
    canvas_widget1.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Close figure when Tkinter window is closed

    # Plot line graph in graph2 frame
    fig2 = plt.figure(figsize=(3, 3), facecolor=graph2['bg'])
    ax2 = fig2.add_subplot()
    ax2.set_facecolor(graph2['bg'])
    ax2.plot(range(1, count+1), total_time_list, marker='x', linestyle='-', color='#17277C')
    ax2.set_xlabel('Product Number')
    ax2.set_ylabel('Total Time')
    ax2.set_title('Total Time for Each Product')

    plt.tight_layout()  # Adjust layout to prevent cutting off labels

    canvas2 = FigureCanvasTkAgg(figure=fig2, master=graph2)
    canvas_widget2 = canvas2.get_tk_widget()
    canvas_widget2.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Close figure when Tkinter window is closed
    def close_figures():
            plt.close(fig1)
            plt.close(fig2)
            window.destroy()

    window.protocol("WM_DELETE_WINDOW", close_figures)

import socket

def export_to_excel():
    global received_data
    # Get the current date in YYYY-MM-DD format
    current_date = datetime.now().strftime("%Y-%m-%d")
    # Define the file name with the current date
    file_name = f"{current_date}.xlsx"
    
    # Create a dictionary to store data in a format suitable for pandas DataFrame
    export_data = {"Station": [], "Time": []}
    for name in received_data:
        for product_num in received_data[name]:
            export_data["Station"].append(product_num)
            export_data["Time"].append(received_data[name][product_num])
    
    # Create a pandas DataFrame from the data
    df = pd.DataFrame(export_data)
    
    # Write the DataFrame to an Excel file
    df.to_excel(file_name, index=False)
    print(f"Data exported to {file_name}")

def receive_data_from_server(name):
    global stop_flag, count, client_socket, received_data, tab_name, num_station_data

    # Reset the necessary variables
    stop_flag = False
    count = 0
    received_data[name] = {}

    HOST = tab_name[name]['HOST']
    PORT = int(tab_name[name]['PORT'])

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        print("Connected to the server.")

        # Receive num_station from the server
        num_station_data = client_socket.recv(1024).decode('utf-8').strip()
        print(f"Received num_station data: {num_station_data}")

        buffer = ""  # Initialize a buffer to store incomplete rows
        while not stop_flag:
            response = client_socket.recv(1024).decode('utf-8')
            if not response:
                break

            buffer += response
            rows = buffer.split('\n')

            # Process each complete row
            for row in rows[:-1]:  # Ignore the last item as it might be incomplete
                row_items = row.split(',')
                if len(row_items) == int(num_station_data) + 1:  # Adjust based on your CSV structure
                    # Use the count as the key and the second item as the value
                    key = count
                    value = row_items[1]  # Get the second item as the value
                    received_data[name][key] = value  # Store the row in the dictionary
                    count += 1  # Increment the count of received rows
                    print(f"Received and stored: {[key, value]}")  # Debug print statement
                elif row_items[0] == "ALL_ROWS_SENT":
                    stop_flag = True  # Stop the loop when all rows are sent
                    print("Received ALL_ROWS_SENT signal, stopping data reception.")
                    break
                else:
                    print(f"Ignored row: {row_items} - Incorrect format")  # Log the incorrect row

            buffer = rows[-1]  # Store the incomplete row for the next iteration

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client_socket:
            client_socket.close()  # Close the socket if it's still open
        print("Disconnected from the server.")
        print(f"Total rows received: {count}")
        print(f"Received data: {received_data}")  # Print the final dictionary


def remove_line():
    def remove(key):
        global tab_name
        del tab_name[key]
        print(f"deleted {key}")
        write_config()
        add_tab()
        master.destroy()

    global tab_name
    master = Tk()
    master.title("Remove Assembly Line")
    master.geometry('450x350')

    title_label = Label(master, text="Remove an Assembly Line", font=("Helvetica", 16, "bold"))
    title_label.pack()

    # Create a canvas and a scrollbar
    canvas = Canvas(master)
    scrollbar = Scrollbar(master, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Pack the canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Create buttons inside the scrollable frame
    for line_name in tab_name.keys():
        new_button = Button(scrollable_frame, text=line_name, width=20, height=2, bd=5, relief="groove", padx=10, command=partial(remove, line_name))
        new_button.pack(pady=5, padx=150)

    master.mainloop()

def load_line(name):
    global name_frame, target_output_label, tab_name
    for widget in name_frame.winfo_children():
        widget.destroy()
    print(f"Button clicked {name}")
    label = Label(name_frame, text=name, font=("Inter", 40, "bold"), background='#D9D9D9')
    label.place(relx=0.5, rely=0.5, anchor="center")
    target_output_label.config(text=tab_name[name]['Target'])

    # Reset the stop flag and start receiving data
    stop_flag = False
    receive_data_from_server(name)
    update_gui(name)


def add_tab():
    global tab_frame
    for widget in tab_frame.winfo_children():
        widget.destroy()
    for line_name in tab_name.keys():
        new_button = Button(tab_frame, text=line_name, width=20, height=3, bd=5, relief="groove", padx=10, command=partial(load_line, line_name))
        new_button.pack(side='left', pady=5)

def add_new_tab():
    def submit():
        line_name = e1.get()
        host = e2.get()
        port = e3.get()
        target=e4.get()

        global tab_name

        # Store entries in a dictionary
        tab_name[line_name] = {
            'HOST': host,
            'PORT': port,
            'Target': target
        }

        print("Submitted:", tab_name)  # Print for demonstration

        # Clear the entry fields after submission
        e1.delete(0, 'end')
        e2.delete(0, 'end')
        e3.delete(0, 'end')

        # Write dictionary to a text file
        write_config()

        add_tab()  # Update the tab buttons
        master.destroy()  # Destroy the window after submission

    master = Tk()
    master.title("Add New Assembly Line")
    master.geometry("450x350")

    title_label = Label(master, text="Add New Assembly Line", font=("Helvetica", 16, "bold"))
    title_label.place(x=104, y=29)

    Label(master, text='Line Name').place(x=79, y=100)
    Label(master, text='HOST:').place(x=79, y=140)
    Label(master, text='PORT:').place(x=79, y=180)
    Label(master, text='TARGET:').place(x=79, y=220)

    submit_button = Button(master, height=2, width=15, relief='solid', bd=2, text='Submit', command=submit)
    submit_button.place(x=180, y=290)

    e1 = Entry(master, width=30)
    e2 = Entry(master, width=30)
    e3 = Entry(master, width=30)
    e4 = Entry(master, width=30)

    e1.place(x=150, y=100)
    e2.place(x=150, y=140)
    e3.place(x=150, y=180)
    e4.place(x=150, y=220)


    mainloop()

def on_closing():
    global stop_flag, window
    stop_flag = True
    window.destroy()

def update(window, id):
    pass

window = Tk()
window.geometry("1300x920")
window.title("Tracking System")

window.protocol("WM_DELETE_WINDOW", on_closing)

Frame1 = Frame(window, height=130, width=1300, background='#009999', bd=5, relief="raised")
graph1 = Frame(window, height=344, width=406, bg='#D9D9D9', bd=2, relief="solid")
graph2 = Frame(window, height=334, width=406, bg='#D9D9D9', bd=2, relief="solid")

tab_frame = Frame(window, height=90, width=1300)


name_frame = Frame(window, height=92, width=844, bg="#D9D9D9", bd=2, relief="solid")
output_frame = Frame(window, height=325, width=268, bg="#D9D9D9", bd=2, relief="solid").place(x='8', y='313')
target_frame = Frame(window, height=325, width=268, bg="#D9D9D9", bd=2, relief="solid").place(x='298', y='313')
Total_time = Frame(window, height=325, width=268, bg="#D9D9D9", bd=2, relief="solid").place(x='584', y='313')

Label(output_frame, text='Total \nOutput', font=("Inter", 30, "bold"), bg="#D9D9D9").place(x='70', y='361')
total_output_label = Label(output_frame, text='000', font=("Inter", 50, "bold"), bg="#D9D9D9")
total_output_label.place(x='80', y='500')

Label(target_frame, text='Targeted \nOutput', font=("Inter", 30, "bold"), bg="#D9D9D9").place(x='340', y='361')
target_output_label = Label(target_frame, text='000', font=("Inter", 50, "bold"), bg="#D9D9D9")
target_output_label.place(x='370', y='500')

Label(target_frame, text='Total \nTime', font=("Inter", 30, "bold"), bg="#D9D9D9").place(x='670', y='361')
total_time_label = Label(target_frame, text='000', font=("Inter", 50, "bold"), bg="#D9D9D9")
total_time_label.place(x='670', y='500')

button1 = Button(window, text='Export to excel', bg="#D9D9D9", width='25', height='3', bd=2, relief="solid", font=("Inter", 12, "bold") ,command=export_to_excel)
button3 = Button(window, text='Add new line', bg="#D9D9D9", width='25', height='3', bd=2, relief="solid", command=add_new_tab, font=("Inter", 12, "bold"))
remove_button = Button(window, text='X', width=5, height=3, bd=2, relief="solid", font=("Inter", 10, "bold"), bg='#8C1B1B', fg='white', padx=0, pady=0, command=remove_line)

siemens = Label(Frame1, text="SIEMENS", font=("Inter", 80 * -1, "bold"), background='#009999', fg='white')

Frame1.place(x=0, y=0)

tab_frame.place(x=0, y=133)
siemens.place(x=15, y=15)
graph1.place(x='874', y='204')
graph2.place(x='874', y='572')
name_frame.place(x='8', y='204')

button1.place(x='125', y='743')
button3.place(x='500', y='743')
remove_button.place(x='1245', y='133')

tab_name = config()
add_tab()

window.mainloop()
