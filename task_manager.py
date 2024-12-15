import time

from colorama import Fore, Style
from datetime import datetime
import sqlite3
import os
import sys

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # For PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_shared_db_path(db_name):
    """
    Get the absolute path to the shared database.
    The database is stored in the user's home directory.
    """
    shared_dir = os.path.expanduser("C:/Users/basel/Desktop/Basel_Files/TM")  # User's home directory
    if not os.path.exists(shared_dir):
        os.makedirs(shared_dir)  # Create the directory if it doesn't exist
    return os.path.join(shared_dir, db_name)

# Define the shared database path
db_path = get_shared_db_path("my_db.db")

conn = sqlite3.connect(db_path)
c = conn.cursor()

class TaskManager:
    def __init__(self):
        self.tasks = []
        self.curr_user = "NULL"
        c.execute("SELECT date FROM reset WHERE id = 1;")
        d = c.fetchone()
        python_date = datetime.strptime(d[0], "%Y-%m-%d").date()
        self.last_reset = python_date


    def task_found(self, to_find):
        for t in self.tasks:
            if t["task"] == to_find:
                return True
        return False

    def add_user(self):
        print(Fore.YELLOW + "\nEnter user name: ", end="" + Fore.RESET)
        u = input()
        if u == "0":
            self.iden()
        if u == "NULL":
            print(Fore.GREEN + "You can't use this name..." + Fore.RESET)
            self.iden()
        # Check if the user already exists
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (u,))
        user_exists = c.fetchone()[0]  # This will return 0 if the user doesn't exist, or 1 if it does.

        if user_exists:
            print(Fore.RED + "User already exists!" + Fore.RESET)
        else:
            # Insert the user if it doesn't exist
            c.execute("INSERT INTO users (user_id) VALUES (?)", (u,))
            conn.commit()
            print(Fore.GREEN + f"User '{u}' added successfully!" + Fore.RESET)

    def login(self):
        print(Fore.YELLOW + "\nEnter user name: ", end = "" + Fore.RESET)
        u = input()
        if u == "0":
            self.iden()
        c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (u,))
        user_exists = c.fetchone()[0]
        if user_exists:
            self.curr_user = u
            c.execute("SELECT task, times_a_day, done, completed, i FROM tasks WHERE user_id = ?", (self.curr_user,))
            self.tasks = c.fetchall()
            self.run()
        else:
            print(Fore.RED + "User doesn't exist!" + Fore.RESET)

    def add_task(self, task, num_a_day):
        c.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (self.curr_user,))
        task_exists = task in c.fetchall()
        if task_exists:
            print(Fore.RED + "Task is already added...")
            self.run()
        if int(num_a_day) < 0:
            print(Fore.RED + "Enter a valid number of days...")
            self.run()
        else:
            c.execute("INSERT INTO tasks (user_id, task, times_a_day, done, completed, i) VALUES (?, ?, ?, ?, ?, ?)",
                         (self.curr_user, task, num_a_day, 0, 0,1001))
            conn.commit()
            self.fix_index()
            conn.commit()
            self.run()
            print(Fore.GREEN + f"Task was added successfully!" + Fore.RESET)

    def fix_index(self):
        curr = self.curr_user
        c.execute("SELECT task, times_a_day, done, completed, i FROM tasks WHERE user_id = ?", (self.curr_user,))
        tasks = c.fetchall()
        index_ = 1
        tasks = sorted(tasks, key=lambda x: x[4])
        for t in tasks:
            c.execute("Update tasks SET i = ? WHERE user_id = ? AND task = ?", (index_, curr, t[0],))
            conn.commit()
            index_ += 1

    def view_tasks(self):
        curr = self.curr_user
        c.execute("SELECT task, times_a_day, done, completed, i FROM tasks WHERE user_id = ?", (self.curr_user,))
        tasks = c.fetchall()

        if not tasks:
            print(Fore.RED + "No tasks available.")
            return -1
        print(Fore.CYAN + "\nTask List:")

        index_ = 1
        tasks = sorted(tasks, key=lambda x: x[4])
        for t in tasks:
            # ✔
            status = "🗸" if t[3] else "✘"
            d = t[2]
            num = t[1]
            if d < t[1]:
                print(Fore.RED + f"{index_}. [ {status} ] {t[0]} ({d}/{num})")
            else:
                print(Fore.GREEN + f"{index_}. [ {status} ] {t[0]} ({d}/{num})")
            c.execute("Update tasks SET i = ? WHERE user_id = ? AND task = ?", (index_, curr, t[0],))
            conn.commit()
            index_ += 1
        return 0

    def mark_task_completed(self, task_number):
        curr = self.curr_user
        c.execute("SELECT task, times_a_day, done, completed, i FROM tasks WHERE user_id = ?", (curr,))
        tasks = c.fetchall()
        
        if 0 < task_number <= len(tasks):
            c.execute("SELECT task, times_a_day, done, completed, i FROM tasks WHERE user_id = ? AND i = ?", (self.curr_user, task_number,))
            t = c.fetchall()[0]
            if t[2] == t[1]:
                print(Fore.GREEN + "Task is already completed..." + Fore.RESET)
            else:
                a = t[1]
                d = t[2]
                c.execute("Update tasks SET done = ? WHERE user_id = ? AND task = ?", (d + 1, curr, t[0],))
                conn.commit()
                if a == (d + 1):
                    c.execute("Update tasks SET completed = ? WHERE user_id = ? AND task = ?", (1, curr, t[0],))
                    conn.commit()
                print(Fore.GREEN + "Task marked as completed!")
                self.view_tasks()
        else:
            print(Fore.RED + "Invalid task number.")

    def edit_task_name(self, task_number, new_name):
        curr = self.curr_user
        c.execute("SELECT task, times_a_day, done, completed, i FROM tasks WHERE user_id = ?", (curr,))
        tasks = c.fetchall()

        # we still have to check if the new name isn't already used !!

        if 0 < task_number <= len(tasks):
            c.execute("Update tasks SET task = ? WHERE user_id = ? AND i = ?", (new_name, curr, task_number,))
            conn.commit()
            # self.view_tasks()
            print(Fore.GREEN + "\nTask edited successfully!")
        else:
            print(Fore.RED + "\nInvalid task number.")

    def edit_num_a_day(self, task_number, new_num):
        curr = self.curr_user
        c.execute("SELECT task, times_a_day, done, completed, i FROM tasks WHERE user_id = ?", (curr,))
        tasks = c.fetchall()

        # we still have to check if the new num is less that done + if it is negative!!

        if 0 < task_number <= len(tasks):
            c.execute("Update tasks SET times_a_day = ? WHERE user_id = ? AND i = ?", (new_num, curr, task_number,))
            conn.commit()
            # self.view_tasks()
            print(Fore.GREEN + "\nTask edited successfully!")
        else:
            print(Fore.RED + "Invalid task number.")

    def delete_task(self, task_number):
        curr = self.curr_user
        c.execute("SELECT task, times_a_day, done, completed, i FROM tasks WHERE user_id = ?", (curr,))
        tasks = c.fetchall()

        if 0 < task_number <= len(tasks):
            c.execute("DELETE FROM tasks WHERE user_id = ? AND i = ?", (curr, task_number,))
            conn.commit()
            self.fix_index()
            conn.commit()
            print(Fore.GREEN + "\nThe task was deleted successfully!")
        else:
            print(Fore.RED + "Invalid task number.")

    def delete_account(self):
        curr = self.curr_user
        c.execute("DELETE FROM tasks WHERE user_id = ?", (curr,))
        c.execute("DELETE FROM users WHERE user_id = ?", (curr,))
        conn.commit()
        print(Fore.GREEN + "\nThe account was deleted successfully!")
        self.iden()

    def run(self):
        while True:
            print(Fore.CYAN + Style.BRIGHT + "\nTask Manager:")
            print(Fore.WHITE + Style.BRIGHT + "1. Add Task")
            print("2. View Tasks")
            print("3. Mark Task as Completed")
            print("4. Edit Task")
            print("5. Edit Number of Times a Day for a Task")
            print("6. Delete Task")
            print("7. Delete Account")
            print("8. Log Out")
            print("9. Exit")
            print(Fore.YELLOW + "\nChoose an option: ", end="" + Fore.RESET)
            choice = input()

            if choice == "1":
                print(Fore.YELLOW + "- Enter 0 to undo -")
                print(Fore.YELLOW + "\nEnter the task: ", end="" + Fore.RESET)
                t = input()
                if t == "0":
                    self.run()
                print (Fore.YELLOW + "Enter number of times a day: ", end="" + Fore.RESET)
                num = input()
                if num == "0":
                    self.run()
                self.add_task(t, num)
            elif choice == "2":
                self.view_tasks()
            elif choice == "3":
                if self.view_tasks() == -1:
                    continue
                print(Fore.YELLOW + "\n- Enter 0 to undo -")
                print(Fore.YELLOW + "\nEnter the task number to mark as completed: ", end="" + Fore.RESET)
                task_number = int(input())
                if task_number == 0:
                    self.run()
                self.mark_task_completed(task_number)
            elif choice == "4":
                if self.view_tasks() == -1:
                    continue
                print(Fore.YELLOW + "- Enter 0 to undo -")
                print(Fore.YELLOW + "\nEnter the task number to edit: ", end="" + Fore.RESET)
                task_number = int(input())
                if task_number == 0:
                    self.run()
                print(Fore.YELLOW + "Enter the edited task: ", end="" + Fore.RESET)
                new_name = input()
                if new_name == "0":
                    self.run()
                self.edit_task_name(task_number, new_name)
            elif choice == "5":
                print(Fore.YELLOW + "- Enter 0 to undo -")
                if self.view_tasks() == -1:
                    continue
                print(Fore.YELLOW + "\nEnter the task number to edit: ", end="" + Fore.RESET)
                task_number = int(input())
                if task_number == 0:
                    self.run()
                print(Fore.YELLOW + "Enter the edited number: ", end="" + Fore.RESET)
                new_num = input()
                if new_num == "0":
                    self.run()
                self.edit_num_a_day(task_number, new_num)
            elif choice == "6":
                print(Fore.YELLOW + "- Enter 0 to undo -")
                if self.view_tasks() == -1:
                    continue
                print(Fore.YELLOW + "\nEnter the task number to delete: ", end="" + Fore.RESET)
                task_number = int(input())
                if task_number == 0:
                    self.run()
                self.delete_task(task_number)
            elif choice == "7":
                self.delete_account()
            elif choice == "8":
                print(Fore.RED + "Logging Out!")
                self.curr_user = "NULL"
                self.iden()
            elif choice == "9":
                print(Fore.RED + "\nExiting Task Manager. Goodbye!")
                time.sleep(0.75)
                if conn:
                    conn.close()
                sys.exit(0)
            else:
                print(Fore.RED + "Option \"" + choice + "\" is not available.")

    def iden(self):
        now = datetime.now().date()

        if self.last_reset != now:
            c.execute("DELETE FROM tasks;")
            conn.commit()
            self.last_reset = now
            x = now.strftime("%Y-%m-%d")
            c.execute("Update reset SET date = ? WHERE id = ?", (x, 1, ))
            conn.commit()

        while True:
            print(Fore.CYAN + Style.BRIGHT + "\nPlease Identify to use Task Manager:" + Fore.RESET)
            print(Fore.WHITE + Style.BRIGHT + "1. Login")
            print("2. Sign Up")
            print("3. Exit")

            print(Fore.YELLOW + "\nChoose an option: ", end ="" + Fore.RESET)
            choice = input()
            # choice = input(Fore.YELLOW + "\nChoose an option: ")

            if choice == "1":
                print(Fore.YELLOW + "- Enter 0 to undo -")
                self.login()
            elif choice == "2":
                print(Fore.YELLOW + "- Enter 0 to undo -")
                self.add_user()
            elif choice == "3":
                print(Fore.RED + "\nExiting Task Manager. Goodbye!")
                time.sleep(0.75)
                if conn:
                    conn.close()
                sys.exit(0)
            else:
                print(Fore.RED + "Option \"" + choice + "\" is not available.")

if __name__ == "__main__":
    manager = TaskManager()
    manager.iden()
