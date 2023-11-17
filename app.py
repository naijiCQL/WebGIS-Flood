# -*- coding: utf-8 -*-
import os
import threading
import time
import tkinter as tk
import tkinter.messagebox as messagebox
import webbrowser
from datetime import datetime, timedelta
from tkinter import filedialog
import h5py
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, render_template
from osgeo import gdal
from scipy.interpolate import griddata
from werkzeug.serving import make_server
from decimal import Decimal

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class HECRASController:
    def __init__(self):
        # 初始化HECRAS控制器对象
        import win32com.client
        self.hec = win32com.client.Dispatch("RAS507.HECRASController")

    def open_project(self, project_path):
        # 打开HEC-RAS项目
        self.hec.Project_Open(project_path)
        # self.hec.ShowRas()

    def close(self):
        # 关闭HECRAS
        self.hec.Quit()

    def edit_unsteady_flow_data(self):
        # 打开非恒定流数据窗口
        self.hec.Edit_UnsteadyFlowData()

    def edit_plan_data(self):
        # 打开计算窗口
        self.hec.Edit_PlanData()

    def show_ras_mapper(self):
        # 打开RAS Mapper
        self.hec.ShowRasMapper()

    def export_tiff_data(self):
        # 打开HDF文件并读取x、y和高度值
        filename = "D:/HEC-RAS/exercise/2023-3-22/2d-demo/river.p01.hdf"
        f = h5py.File(filename, "r")

        coordinates = f["Geometry"]["2D Flow Areas"]["Perimeter 1"]["Cells Center Coordinate"]

        depth_data = \
            f["Results"]["Unsteady"]["Output"]["Output Blocks"]["Base Output"]["Unsteady Time Series"]["2D Flow Areas"][
                "Perimeter 1"]["Depth"]

        x = coordinates[:, 0]
        y = coordinates[:, 1]
        time_steps = depth_data.shape[0]

        # 打开现有的Tiff文件获取栅格信息
        existing_tiff = "D:/HEC-RAS/python_arcgis/data/dem_data/20.Terrain.DEM.tif"
        existing_ds = gdal.Open(existing_tiff)
        rows = existing_ds.RasterYSize
        cols = existing_ds.RasterXSize
        geotransform = existing_ds.GetGeoTransform()
        projection = existing_ds.GetProjection()

        def interpolate_height(x, y, height, geotransform, rows, cols):
            # 构建目标栅格的网格坐标
            xx, yy = np.meshgrid(np.linspace(geotransform[0], geotransform[0] + geotransform[1] * cols, cols),
                                 np.linspace(geotransform[3] + geotransform[5] * rows, geotransform[3], rows))

            # 进行双线性插值
            height_interp = griddata((x, y), height, (xx, yy), method='linear')

            # 垂直翻转高度插值结果
            height_interp = np.flipud(height_interp)

            return height_interp

        window = tk.Tk()
        window.title("处理进度")

        # 获取屏幕宽度和高度
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # 设置窗口的宽度和高度
        window_width = 300
        window_height = 30

        # 计算窗口的位置
        x1 = (screen_width - window_width) // 2
        y1 = (screen_height - window_height) // 2

        # 设置窗口的位置
        window.geometry(f"{window_width}x{window_height}+{x1}+{y1}")

        # 创建标签用于显示消息
        label = tk.Label(window, text="", width=30)
        label.pack()

        def update_message(current_step, total_steps):
            message = f"第 {current_step}/{total_steps} 已创建完成"
            label.config(text=message)
            window.update()

        for i in range(time_steps - 5, time_steps):
            height = depth_data[i, :]

            output_tiff = f"D:/HEC-RAS/exercise/2023-3-22/2d-demo/01/data/{i + 1}.tif"
            driver = gdal.GetDriverByName("GTiff")
            new_ds = driver.Create(output_tiff, cols, rows, 1, gdal.GDT_Float32)

            new_ds.SetGeoTransform(geotransform)
            new_ds.SetProjection(projection)

            height_interp = interpolate_height(x, y, height, geotransform, rows, cols)

            band = new_ds.GetRasterBand(1)
            band.WriteArray(height_interp)

            band.ComputeStatistics(False)
            new_ds.FlushCache()
            new_ds = None
            print(f"第 {i + 1}/{depth_data.shape[0]} 已创建完成")
            update_message(i + 1, time_steps)

        f.close()

        existing_ds = None

        messagebox.showinfo("处理完成", "各步长的tiff文件已全部导出")
        window.destroy()

    def export_kmz_data(self):
        exe_path = r"D:\HEC-RAS\cql\demo1\dist\main.exe"
        os.system(exe_path)
        messagebox.showinfo("处理完成", "各步长的tiff文件已预处理完毕")

    def connect_webgis(self):
        url = 'http://127.0.0.1:5000/'

        def run_flask_app():
            app = Flask(__name__)

            @app.route('/')
            def index():
                return render_template('index.html')

            server = make_server('127.0.0.1', 5000, app)
            server.serve_forever()

        flask_thread = threading.Thread(target=run_flask_app)
        flask_thread.start()

        webbrowser.open(url)

    def run_xaj_model(self):
        exe_path = r"D:\flood-demo\新安江模型\xaj-c++\Example\XAJ.exe"
        os.system(exe_path)
        messagebox.showinfo("运行完成", "预测径流量已产生")

    def show_xaj_result(self):
        input_file = r"D:\flood-demo\新安江模型\xaj-c++\Example\P.txt"
        file_path3 = r"D:\flood-demo\新安江模型\xaj-c++\Example\P1.txt"

        # 读取输入文件并处理数据
        with open(input_file, 'r') as f:
            lines = f.readlines()[1:]  # 跳过第一行

        data = []
        for line in lines:
            row = line.strip().split()
            row_sum = sum(Decimal(value) for value in row)
            data.append(str(row_sum))

        # 将处理后的数据保存到输出文件
        with open(file_path3, 'w') as f:
            f.write('\n'.join(data))

        file_path = r"D:\flood-demo\新安江模型\xaj-c++\Example\Q.txt"
        file_path2 = r"D:\flood-demo\新安江模型\xaj-c++\Example\Q1.txt"

        # 读取第一个文件
        with open(file_path, 'r') as file:
            data = file.readlines()
        # 提取第一个文件的数据
        y_data = [float(line.strip()) for line in data]

        # 读取第二个文件
        with open(file_path2, 'r') as file:
            data2 = file.readlines()
        # 提取第二个文件的数据
        y_data2 = [float(line.strip()) for line in data2]

        # 读取第三个文件
        with open(file_path3, 'r') as file:
            data3 = file.readlines()
        # 提取第三个文件的数据
        y_data3 = [float(line.strip()) for line in data3]

        # 生成横坐标数据
        start_date = datetime(2012, 1, 1)
        num_days = len(y_data)  # 数据的总天数
        date_list = [start_date + timedelta(hours=i) for i in range(num_days)]

        # 生成横坐标刻度标签
        x_ticks = range(num_days)
        x_tick_labels = [date.strftime('%Y/%m/%d') for date in date_list]

        # 设置图形的大小
        fig, ax1 = plt.subplots(figsize=(15, 7))
        plt.rcParams['font.family'] = ['SimHei']

        # 绘制图表
        ax1.plot(x_ticks, y_data)
        ax1.plot(x_ticks, y_data2)
        ax1.legend(['预测流量', '实测流量'])
        ax1.set_xlabel('时间', size=12)
        ax1.set_ylabel('径流量（m^3/s）', size=12)
        ax1.set_title('预测流量', size=16)

        # 设置x轴刻度
        ax1.set_xticks(x_ticks[::96])
        ax1.set_xticklabels(x_tick_labels[::96], rotation=45, size=8)
        ax1.set_ylim(0)

        # 创建第二个坐标轴
        ax2 = ax1.twinx()
        ax2.bar(x_ticks, y_data3, color='green', alpha=0.7)
        ax2.set_ylabel('降雨量（mm）', size=12)
        ax2.set_ylim(ax2.get_ylim()[::-1])  # 反转纵坐标轴的刻度范围
        ax2.yaxis.tick_right()  # 将刻度放置在右边

        # 调整布局，防止刻度标签重叠
        plt.tight_layout()

        plt.show()


# 创建GUI界面
class App:

    def __init__(self, master):
        self.master = master
        master.title("Automated XAJ,HEC-RAS program for flood forecasting")

        # 创建左侧容器
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        # 创建上方区域
        top_label = tk.Label(self.left_frame, text='Auto XAJ', font=('Arial', 12, 'bold'), fg='dodgerblue')
        top_label.pack(pady=10)

        top_frame = tk.Frame(self.left_frame, bd=2, relief=tk.GROOVE)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 创建下方区域
        bottom_label = tk.Label(self.left_frame, text='Auto HEC-RAS', font=('Arial', 12, 'bold'), fg='limegreen')
        bottom_label.pack(pady=10)

        bottom_frame = tk.Frame(self.left_frame, bd=2, relief=tk.GROOVE)
        bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 创建打开项目按钮
        self.open_button = tk.Button(bottom_frame, text="1-打开项目", command=self.open_project, width=25)
        self.open_button.pack(pady=(0, 5))

        # 创建打开非恒定流数据窗口按钮
        self.edit_unsteady_flow_data_button = tk.Button(bottom_frame, text="2-边界条件编辑窗口",
                                                        command=self.edit_unsteady_flow_data, width=25)
        self.edit_unsteady_flow_data_button.pack(pady=5)

        # 创建打开计算窗口按钮
        self.edit_plan_data_button = tk.Button(bottom_frame, text="3-计算窗口", command=self.edit_plan_data,
                                               width=25)
        self.edit_plan_data_button.pack(pady=5)

        # 打开RAS Mapper按钮
        self.show_ras_mapper_button = tk.Button(bottom_frame, text="4-结果查看窗口", command=self.show_ras_mapper,
                                                width=25)
        self.show_ras_mapper_button.pack(pady=5)

        # 导出tiff文件按钮
        self.export_tiff_button = tk.Button(bottom_frame, text="5-导出各步长的tiff文件",
                                            command=self.export_tiff_data, width=25)
        self.export_tiff_button.pack(pady=5)

        # tiff文件处理
        self.export_kmz_button = tk.Button(bottom_frame, text="6-tiff文件处理",
                                           command=self.export_kmz_data, width=25)
        self.export_kmz_button.pack(pady=5)

        # Connect to WebGIS
        self.connect_webgis_button = tk.Button(bottom_frame, text="7-三维淹没效果展示",
                                               command=self.connect_webgis, width=25)
        self.connect_webgis_button.pack(pady=(5, 0))

        # 创建运行新安江模型的按钮
        self.run_xaj_button = tk.Button(top_frame, text="1-运行新安江模型",
                                        command=self.run_xaj_model, width=25)
        self.run_xaj_button.pack(pady=(0, 5))

        # 展示新安江模型预测结果
        self.show_xaj_button = tk.Button(top_frame, text="2-预测径流展示",
                                         command=self.show_xaj_result, width=25)
        self.show_xaj_button.pack(pady=(5, 0))

        # 创建右侧容器
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建标题标签
        self.title_label = tk.Label(self.right_frame, text="工作日志", fg="black",
                                    font=("Courier New", 12, "bold"))
        self.title_label.pack(side=tk.TOP, padx=10, pady=10)

        # 创建日志输出控件
        self.log_text = tk.Text(self.right_frame, bg="white", fg="black", font=("Courier New", 12), width=60)
        self.log_text.pack(side=tk.LEFT, fill=tk.Y, expand=True)

        # 创建滚动条
        self.scrollbar = tk.Scrollbar(self.right_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 将滚动条与日志输出控件关联
        self.log_text.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.log_text.yview)

        # 创建HECRAS控制器对象
        self.hec = HECRASController()

    def open_project(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # 打开HECRAS项目
        project_path = tk.filedialog.askopenfilename(filetypes=(("HECRAS Project files", "*.prj"),))
        self.hec.open_project(project_path)
        self.log_text.insert(tk.END, now_time + " 已打开项目: {}\n".format(project_path))

    def edit_unsteady_flow_data(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # 打开非恒定流数据窗口
        self.hec.edit_unsteady_flow_data()
        self.log_text.insert(tk.END, now_time + " 边界条件编辑窗口已打开\n")

    def edit_plan_data(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # 打开计算窗口
        self.hec.edit_plan_data()
        self.log_text.insert(tk.END, now_time + " 计算窗口已打开\n")

    def show_ras_mapper(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # 打开RAS Mapper窗口
        self.hec.show_ras_mapper()
        self.log_text.insert(tk.END, now_time + " 结果查看窗口已打开\n")

    def export_tiff_data(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.hec.export_tiff_data()
        self.log_text.insert(tk.END, now_time + " 各步长的tiff文件已导出\n")

    def export_kmz_data(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.hec.export_kmz_data()
        self.log_text.insert(tk.END, now_time + " 各步长的tiff文件已转化为kmz文件\n")

    def connect_webgis(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.hec.connect_webgis()
        self.log_text.insert(tk.END, now_time + " 已连接webgis\n")

    def run_xaj_model(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.hec.run_xaj_model()
        self.log_text.insert(tk.END, now_time + " 已成功运行新安江模型\n")

    def show_xaj_result(self):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.hec.show_xaj_result()
        self.log_text.insert(tk.END, now_time + " 预测径流量已展示\n")

    def close(self):
        # 关闭HECRAS
        self.hec.close()
        self.master.quit()


root = tk.Tk()
# 宽*高
root.geometry("830x470")
# 获取屏幕的宽度和高度
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 计算窗口左上角的坐标
x = (screen_width - root.winfo_reqwidth()) / 2
y = (screen_height - root.winfo_reqheight()) / 2

# 设置窗口位置
root.geometry("+%d+%d" % (x, y))
app = App(root)
root.mainloop()
