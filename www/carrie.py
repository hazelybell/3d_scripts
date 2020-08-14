from flask import Flask, render_template
app = Flask(__name__, template_folder='.')

class Status:
    def get_cpu(self):
        with open('/proc/stat') as fh:
            lines = fh.readlines()
        cpu = None
        for line in lines:
            if 'cpu ' in line:
                cpu = line
        cpu = list(map(int, cpu.split()[1:]))
        idle = (cpu[2] + cpu[4]) * 100 / sum(cpu[1:])
        used = 100 - idle
        return f"{used:2.0f}"

    def get_ram(self):
        with open('/proc/meminfo') as fh:
            lines = fh.readlines()
        total = None
        free = None
        buff = None
        cache = None
        for line in lines:
            if 'MemTotal' in line:
                total = int(line.split()[1])
            elif 'MemFree' in line:
                free = int(line.split()[1])
            elif 'Buffers' in line:
                buff = int(line.split()[1])
            elif 'Cached' in line:
                cached = int(line.split()[1])
        used = total - free - buff - cached
        used = used * 100 / total
        return f"{used:2.0f}"

    def __init__(self):
        self.cpu = self.get_cpu()
        self.ram = self.get_ram()

@app.route("/")
def index():
    return render_template(
        'index.html',
        status=Status()
        )

if __name__ == '__main__':
    app.run(debug=True)
