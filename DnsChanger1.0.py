import os  # for executing operating system commands
import json  # for working with JSON files
import psutil  # for accessing system and network information
import socket  # for working with network addresses
import tkinter as tk  # for creating graphical user interfaces
from tkinter import messagebox  # for displaying error and success messages

# Path to the JSON file for saving DNS entries
DNS_FILE = "saved_dns.json"

# Function to identify the first active interface and find the current IPv4 DNS


def get_active_interface_with_dns():
    addrs = psutil.net_if_addrs()  # get network addresses
    stats = psutil.net_if_stats()   # get status of network interfaces

    # Iterate over network interfaces
    for interface, snics in addrs.items():
        # print(interface)   These two prints check which interface is active
        # print(stats[interface].isup)
        # print(addrs.items())
        if stats[interface].isup:  # check if the interface is active
            for snic in snics:
                if snic.family == socket.AF_INET and snic.address != "127.0.0.1":  # this condition checks if the active IPv4 interface is something other than the empty address or localhost
                    try:
                        # This command runs in PowerShell and displays the active interface and DNS. You can check with print.
                        dns_output = os.popen(f'netsh interface ip show dns "{interface}"').read()
                        dns_lines = dns_output.split("\n")  # this command splits the output into multiple lines, making it easier to extract information
                        # print(dns_output)
                        # print(dns_lines)

                        # Below, we create two empty variables to store the DNS entries later
                        preferred_dns = None
                        alternative_dns = None

                        # Using a pre-built function, we index the variable we specified
                        for i, line in enumerate(dns_lines):
                            line = line.strip()  # remove extra spaces
                            # print(line)
                            # The condition below checks if this text is in the output line and executes the algorithm to extract the DNS
                            if "Statically Configured DNS Servers:" in line:
                                # Extract the first IP from this line
                                ip = line.split(":")[-1].strip()
                                # print(ip)
                                if validate_dns(ip):  # validate DNS
                                    preferred_dns = ip
                                    # Check the next line to extract the second IP
                                    next_line = dns_lines[i + 1].strip()
                                    if validate_dns(next_line):
                                        alternative_dns = next_line

                        return interface, preferred_dns, alternative_dns  # return the interface name and DNS entries
                    # Here, it considers the exception error as a variable and prints the error in the shell if it occurs
                    except Exception as e:
                        print(f"Error fetching DNS info: {e}")  # print error if something goes wrong

    return None, None, None  # If no active interface is found, return all three outputs as empty


# DNS validation function
def validate_dns(dns_ip):
    try:
        parts = dns_ip.split(".")  # split the IP into parts
        if len(parts) != 4:  # check if it has 4 parts
            return False

        first_part = int(parts[0])  # convert the first part to a number
        if first_part < 1 or first_part > 233:  # check valid range
            return False

        for part in parts[1:]:
            num = int(part)  # convert the next parts to a number
            if num < 0 or num > 255:  # check valid range
                return False

        return True  # if all checks are validated, it's valid
    except ValueError:
        return False  # if there's an error in converting to number

# DNS change function with validation
def change_dns(preferred_dns, alternative_dns=None):
    if not validate_dns(preferred_dns):  # this condition says if the entered DNS is not valid, show validation error in the program
        messagebox.showerror("Error", "Invalid Preferred DNS. Please enter a valid DNS value.")
        return

    # Get the active interface and current DNS from the function defined above
    interface_name, current_preferred, current_alternative = get_active_interface_with_dns()
    if interface_name is None:  # if no active interface is found
        messagebox.showerror("Error", "No active network interface found.")
        return

    # Set DNS by sending a command via PowerShell
    os.system(f'netsh interface ip set dns name="{interface_name}" source=static addr={preferred_dns}')

    # Only set alternative_dns if it has a value
    if alternative_dns and validate_dns(alternative_dns):
        os.system(f'netsh interface ip add dns name="{interface_name}" addr={alternative_dns} index=2')

    refresh_dns_entries()  # refresh DNS entries
    messagebox.showinfo("Success", f"DNS settings changed successfully for {interface_name}!")  # display success message

# DNS reset function
def reset_dns():
    interface_name, _, _ = get_active_interface_with_dns()  # get the active interface
    if interface_name is None:  # if no active interface is found. This happens in case of bugs or no internet access
        messagebox.showerror("Error", "No active network interface found.")
        return

    os.system(f'netsh interface ip set dns name="{interface_name}" source=dhcp')  # set DNS to DHCP (meaning it will automatically detect the address)
    refresh_dns_entries()  # refresh DNS entries
    messagebox.showinfo("Success", f"DNS settings reset successfully for {interface_name}!")  # display success message

# Save DNS function with validation and name field check
def save_dns(preferred_dns, alternative_dns, dns_name, dns_buttons):
    if not dns_name:  # if no DNS name is entered
        messagebox.showerror("Error", "Please enter a name for the DNS configuration.")
        return

    if not validate_dns(preferred_dns):  # validate DNS
        messagebox.showerror("Error", "Invalid Preferred DNS. Please enter a valid DNS value.")
        return

    if alternative_dns and not validate_dns(alternative_dns):  # validate alternative DNS
        messagebox.showerror("Error", "Invalid Alternative DNS. Please enter a valid DNS value.")
        return

    dns_data = load_saved_dns()  # load saved DNS entries
    if len(dns_data) >= 6:  # if the number of saved DNS reaches the maximum
        messagebox.showwarning("Limit Reached", "You can only save up to 6 DNS configurations.")
        return

    dns_data[dns_name] = {"preferred": preferred_dns, "alternative": alternative_dns}  # save DNS data
    save_dns_to_file(dns_data)  # save data to file
    update_dns_buttons(dns_data, dns_buttons)  # update DNS buttons

# Load saved DNS function
def load_saved_dns():
    if os.path.exists(DNS_FILE):  # check for file existence
        with open(DNS_FILE, "r") as file:
            data = json.load(file)  # load data from file
            if isinstance(data, dict):  # this function takes two parameters and checks if the first parameter is of the type of the second parameter. If positive, it returns data for the program
                return data
    return {}  # if the file does not exist, return an empty dictionary

# Save DNS to file function
def save_dns_to_file(dns_data):
    with open(DNS_FILE, "w") as file:  # this Python function specifies that it should open the entered data and save it with the file name, and also be ready to make changes
        json.dump(dns_data, file)  # save data to file

# Delete DNS function on right click
def delete_dns(dns_name, dns_buttons):
    dns_data = load_saved_dns()  # load saved DNS entries
    if dns_name in dns_data:  # if DNS name exists in data
        del dns_data[dns_name]  # delete DNS
        save_dns_to_file(dns_data)  # update file
        update_dns_buttons(dns_data, dns_buttons)  # update DNS buttons

def update_dns_buttons(dns_data, dns_buttons):
    # Function to set up buttons
    def setup_button(button, dns_name):
        button.config(text=dns_name, command=lambda: apply_dns(dns_data[dns_name]))  # This line sets the button logic, and whenever the button is clicked, the lambda function displays the specified function and outputs
        button.grid(row=5 + dns_buttons.index(button), column=0, columnspan=2, pady=2)  # This line sets the button size
        button.bind("<Button-3>", lambda event: show_context_menu(event, dns_name, dns_buttons))  # This code is for right-clicking and sending information to it

    for i, button in enumerate(dns_buttons):
        if i < len(dns_data):
            dns_name = list(dns_data.keys())[i]
            setup_button(button, dns_name)  # call the button setup function
        else:
            button.grid_remove()  # hide excess buttons


# Right-click context menu function
def show_context_menu(event, dns_name, dns_buttons):
    context_menu = tk.Menu(root, tearoff=0)  # create a new menu
    context_menu.add_command(label="Delete", command=lambda: delete_dns(dns_name, dns_buttons))  # add delete option
    context_menu.post(event.x_root, event.y_root)  # display menu at click location

# Apply DNS function
def apply_dns(dns_info):
    change_dns(dns_info['preferred'], dns_info['alternative'])  # Here, a parameter with the specified dictionary format is passed to the main function to apply changes to DNS. This makes the code more readable.

# Refresh DNS entries function
def refresh_dns_entries():
    _, current_preferred, current_alternative = get_active_interface_with_dns()  # get current DNS entries
    preferred_dns_entry.delete(0, tk.END)  # clear the main DNS input
    if current_preferred:
        preferred_dns_entry.insert(0, current_preferred)  # insert the main DNS into input

    alternative_dns_entry.delete(0, tk.END)  # clear the alternative DNS input
    if current_alternative:
        alternative_dns_entry.insert(0, current_alternative)  # insert the alternative DNS into input

# Create GUI with display of current IPv4 DNS
def create_gui():
    global root, preferred_dns_entry, alternative_dns_entry  # define global variables
    root = tk.Tk()  # create the main window
    root.title("DNS Changer")  # window title

    # Set dark theme
    root.configure(bg="#2E2E2E")  # dark background color

    # Set text color
    text_color = "#FFFFFF"  # white text color

    # Load PNG image
    icon_image = tk.PhotoImage(file="Enter your picture path here!!")  # load image
    root.iconphoto(False, icon_image)  # set window icon

    # Center the window
    window_width = 287  # window width
    window_height = 290  # window height
    screen_width = root.winfo_screenwidth()  # screen width
    screen_height = root.winfo_screenheight()  # screen height
    x_position = (screen_width // 2) - (window_width // 2)  # calculate horizontal position
    y_position = (screen_height // 2) - (window_height // 2)  # calculate vertical position
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")  # set window size and position

    interface_name, current_preferred, current_alternative = get_active_interface_with_dns()  # get current DNS entries

    preferred_dns_label = tk.Label(root, text="Preferred DNS:", bg="#2E2E2E", fg=text_color)  # preferred DNS label
    preferred_dns_label.grid(row=0, column=0)  # place text at row 0, column 0

    preferred_dns_entry = tk.Entry(root)  # input for preferred DNS
    preferred_dns_entry.grid(row=0, column=1)  # place input at row 0, column 1
    if current_preferred:
        preferred_dns_entry.insert(0, current_preferred)  # insert preferred DNS into input

    alternative_dns_label = tk.Label(root, text="Alternative DNS:", bg="#2E2E2E", fg=text_color)  # alternative DNS label
    alternative_dns_label.grid(row=1, column=0)  # place text at row 1, column 0

    alternative_dns_entry = tk.Entry(root)  # input for alternative DNS
    alternative_dns_entry.grid(row=1, column=1)  # place input at row 1, column 1
    if current_alternative:
        alternative_dns_entry.insert(0, current_alternative)  # insert alternative DNS into input

    dns_name_label = tk.Label(root, text="DNS Name:", bg="#2E2E2E", fg=text_color)  # DNS name label
    dns_name_label.grid(row=2, column=0)  # place label at row 2, column 0

    dns_name_entry = tk.Entry(root)  # input for DNS name
    dns_name_entry.grid(row=2, column=1)  # place input at row 2, column 1

    dns_buttons = []  # list of buttons
    for i in range(6):  # here the range is set to six to finally insert six buttons
        button = tk.Button(root, text="", width=20, bg="#444444", fg=text_color)  # create button
        button.grid(row=5 + i, column=0, columnspan=2, pady=2)  # place buttons
        button.grid_remove()  # initially hide buttons
        dns_buttons.append(button)  # add button to list
        for i, button in enumerate(dns_buttons):
            button.grid(row=5 + i, column=0, columnspan=1, pady=2, padx=(50, 0))  # this code was taken from chat GPT to center the DNS buttons in the program

    change_dns_button = tk.Button(root, text="Change DNS", bg="#666666", fg=text_color,
                                  command=lambda: change_dns(preferred_dns_entry.get(), alternative_dns_entry.get()))  # change DNS button
    change_dns_button.grid(row=3, column=0)  # place button at row 3, column 0

    save_dns_button = tk.Button(root, text="Save DNS", bg="#666666", fg=text_color,
                                command=lambda: save_dns(preferred_dns_entry.get(), alternative_dns_entry.get(),
                                                         dns_name_entry.get(), dns_buttons))  # save DNS button
    save_dns_button.grid(row=3, column=1)  # place button at row 3, column 1

    reset_dns_button = tk.Button(root, text="Reset DNS", bg="#666666", fg=text_color, command=reset_dns)  # reset DNS button
    reset_dns_button.grid(row=3, column=2)  # place button at row 3, column 2

    # Active DNS refresh button
    refresh_button = tk.Button(root, text="↻", bg="#666666", fg=text_color, command=refresh_dns_entries)  # refresh button
    refresh_button.grid(row=0, column=2, padx=5, pady=5)  # place button at row 0, column 2

    dns_data = load_saved_dns()  # load saved DNS entries
    update_dns_buttons(dns_data, dns_buttons)  # update DNS buttons

    # Disable window resizing
    root.resizable(False, False)  # disable window resizing

    root.mainloop()  # start the main program loop


create_gui()  # call the function to create the user interface


# Also you can make an exe app using this in ide terminal or code directory terminal

# pyinstaller --onefile --icon="put your .ico image format path here  to set a logo for your app" --windowed  DnsChanger1.0.py

# @R4m71n (: