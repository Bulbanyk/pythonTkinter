import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk, Listbox, MULTIPLE
import subprocess
import threading
import sys
import io
import os
import datetime


class StreamToTkinter(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Прокручиваем текст вниз


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Тестовое задание")
        self.files_history = []  # История файлов
        self.processes = {}  # Словарь для хранения процессов по имени файла

        # Создание вкладок
        self.tab_control = ttk.Notebook(root)

        # Вкладка вывода
        self.output_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.output_tab, text="Вывод")

        # Вкладка логов
        self.logs_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.logs_tab, text="Логи")

        # Вкладка истории файлов
        self.history_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.history_tab, text="История файлов")

        self.tab_control.pack(expand=1, fill="both")

        # Кнопка очистки вывода под окном вывода
        self.clear_button = tk.Button(self.output_tab, text="Очистить вывод", command=self.clear_output)
        self.clear_button.pack(padx=10, pady=5, side=tk.BOTTOM)

        # Окно вывода программ
        self.text_area = scrolledtext.ScrolledText(self.output_tab, wrap=tk.WORD, height=10)
        self.text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        # Добавляем фрейм для списка файлов и скроллбара
        self.file_frame = tk.Frame(self.output_tab)
        self.file_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Список файлов для выбора с поддержкой скроллинга
        self.file_listbox = Listbox(self.file_frame, selectmode=MULTIPLE, height=5)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Добавляем скроллбар к списку файлов
        self.file_scrollbar = tk.Scrollbar(self.file_frame, orient="vertical")
        self.file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=self.file_scrollbar.set)
        self.file_scrollbar.config(command=self.file_listbox.yview)

        # Кнопки в строку
        self.button_frame = tk.Frame(self.output_tab)
        self.button_frame.pack(padx=10, pady=5)

        # Первая строка с кнопками
        self.load_button = tk.Button(self.button_frame, text="Загрузить файлы", command=self.load_files)
        self.load_button.grid(row=0, column=0, padx=5)

        self.delete_button = tk.Button(self.button_frame, text="Удалить файл", command=self.delete_file)
        self.delete_button.grid(row=0, column=1, padx=5)

        # Вторая строка с кнопками
        self.run_button = tk.Button(self.button_frame, text="Запустить выбранные файлы",
                                    command=self.run_selected_scripts, state=tk.DISABLED)
        self.run_button.grid(row=1, column=0, padx=5, pady=10)

        self.stop_button = tk.Button(self.button_frame, text="Остановить выбранные файлы",
                                     command=self.stop_selected_scripts, state=tk.DISABLED)
        self.stop_button.grid(row=1, column=1, padx=5)


        # Вкладка логов, текст
        self.logs_area = scrolledtext.ScrolledText(self.logs_tab, wrap=tk.WORD)
        self.logs_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Кнопка очистки текста
        self.clear_logs_button = tk.Button(self.logs_tab, text="Очистить логи", command=self.clear_logs)
        self.clear_logs_button.pack(pady=5)


        # Вкладка истории файлов, текст
        self.history_area = scrolledtext.ScrolledText(self.history_tab, wrap=tk.WORD)
        self.history_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Кнопка очистки истории файлов
        self.clear_history_button = tk.Button(self.history_tab, text="Очистить историю", command=self.clear_history)
        self.clear_history_button.pack(pady=5)

        self.script_files = []  # Множественный выбор файлов
        self.threads = []  # Для потоков

        # Перенаправим стандартный вывод
        sys.stdout = StreamToTkinter(self.text_area)

    def get_current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def clear_history(self):
        self.history_area.config(state=tk.NORMAL)
        self.history_area.delete(1.0, tk.END)  # Очистка текстового виджета истории файлов
        self.history_area.config(state=tk.DISABLED)

    def load_files(self):
        # Открытие диалога для выбора нескольких файлов
        new_files = filedialog.askopenfilenames(defaultextension=".py", filetypes=[("Python files", "*.py")])
        if new_files:
            self.run_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            # Добавляем файлы в список, если их там ещё нет
            for file in new_files:
                if file not in self.script_files:
                    self.script_files.append(file)
                    self.file_listbox.insert(tk.END, file)
                    self.files_history.append(file)
                    self.history_area.config(state=tk.NORMAL)
                    self.history_area.insert(tk.END, f"{self.get_current_time()} - Загружен файл: {file}\n")
                    self.history_area.config(state=tk.DISABLED)
            messagebox.showinfo("Информация", "Файлы загружены.")

    def delete_file(self):
        selected_file_indices = self.file_listbox.curselection()
        if selected_file_indices:
            for index in reversed(selected_file_indices):
                script_file = self.file_listbox.get(index)
                self.file_listbox.delete(index)  # Удаляем файл из списка
                self.script_files.remove(script_file)  # Удаляем файл из внутреннего списка

                # Добавляем уведомление об удалении в историю
                self.history_area.config(state=tk.NORMAL)
                self.history_area.insert(tk.END, f"{self.get_current_time()} - Удалён файл: {script_file}\n")
                self.history_area.config(state=tk.DISABLED)

    def run_selected_scripts(self):
        selected_file_indices = self.file_listbox.curselection()
        if selected_file_indices:
            for index in selected_file_indices:
                script_file = self.file_listbox.get(index)
                if script_file not in self.processes:
                    process = subprocess.Popen(['python', script_file],
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE,
                                               text=True,
                                               encoding='utf-8')  # Задаём кодировку UTF-8
                    self.processes[script_file] = process
                    thread = threading.Thread(target=self.read_output, args=(process, script_file), daemon=True)
                    self.threads.append(thread)
                    thread.start()
                    self.logs_area.config(state=tk.NORMAL)
                    self.logs_area.insert(tk.END, f"{self.get_current_time()} - Запущен скрипт: {script_file}\n")
                    self.logs_area.config(state=tk.DISABLED)

    def read_output(self, process, script_file):
        self.logs_area.config(state=tk.NORMAL)
        self.logs_area.insert(tk.END, f"{self.get_current_time()} - Выполнение скрипта: {script_file}\n")
        self.logs_area.config(state=tk.DISABLED)

        # Чтение стандартного вывода
        while True:
            output = process.stdout.readline()  # Используем readline для построчного чтения
            if output == '' and process.poll() is not None:
                break
            if output:
                output_str = f"[{os.path.basename(script_file)}]: {output.strip()}\n"
                print(output_str, end='')  # выводим с указанием файла
                self.logs_area.config(state=tk.NORMAL)
                self.logs_area.insert(tk.END, output_str)
                self.logs_area.config(state=tk.DISABLED)

        # Проверка стандартных ошибок
        stderr_output = process.stderr.read()
        if stderr_output:
            error_str = f"[{os.path.basename(script_file)}]: {stderr_output.strip()}\n"
            print(error_str, end='')
            self.logs_area.config(state=tk.NORMAL)
            self.logs_area.insert(tk.END, error_str)
            self.logs_area.config(state=tk.DISABLED)

        # Удаляем процесс из словаря только если он ещё не был удалён вручную
        if script_file in self.processes:
            del self.processes[script_file]

    def stop_selected_scripts(self):
        selected_file_indices = self.file_listbox.curselection()
        if selected_file_indices:
            for index in selected_file_indices:
                script_file = self.file_listbox.get(index)
                if script_file in self.processes:
                    process = self.processes[script_file]
                    process.terminate()
                    print(f"Скрипт {script_file} остановлен.")
                    self.logs_area.config(state=tk.NORMAL)
                    self.logs_area.insert(tk.END, f"{self.get_current_time()} - Скрипт {script_file} остановлен.\n")
                    self.logs_area.config(state=tk.DISABLED)

                    # Удаляем процесс только если он существует
                    if script_file in self.processes:
                        del self.processes[script_file]

    def clear_output(self):
        self.text_area.delete(1.0, tk.END)  # Очистка текстового виджета

    def clear_logs(self):
        self.logs_area.config(state=tk.NORMAL)
        self.logs_area.delete(1.0, tk.END)  # Очистка текстового виджета логов
        self.logs_area.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
