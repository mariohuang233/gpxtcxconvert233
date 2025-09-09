# GPX转TCX工具使用指南

## 🎯 工具简介

这是一个专门将GPX文件转换为TCX文件的工具，**无需原始TCX文件**，只需要GPX轨迹就能生成完整的运动数据文件。

### 适用场景
- 只有GPS轨迹记录，需要上传到运动平台
- 想要为GPX轨迹添加心率、步频、功率等运动数据
- 需要将GPX格式转换为更通用的TCX格式
- 运动设备只能导出GPX，但平台需要TCX格式

## 🚀 快速开始

### 1. 检查工具是否正常
```bash
python3 test_gpx_to_tcx.py
```

### 2. 查看帮助信息
```bash
python3 gpx_to_tcx.py --help
```

### 3. 查看使用示例
```bash
python3 gpx_to_tcx.py --examples
```

### 4. 最简单的转换
```bash
python3 gpx_to_tcx.py 你的路线.gpx -o 生成的运动.tcx
```

## 📖 详细使用说明

### 基本语法
```bash
python3 gpx_to_tcx.py <GPX文件> -o <输出TCX文件> [可选参数]
```

### 参数说明

#### 必需参数
- `GPX文件`: 输入的GPX文件路径
- `-o, --output`: 输出的TCX文件路径

#### 心率参数
- `--base-hr`: 基础心率 (默认: 120 bpm)
- `--max-hr`: 最大心率 (默认: 180 bpm)
- `--hr-factor`: 心率调整系数 (默认: 1.5)

#### 步频参数
- `--base-cadence`: 基础步频 (默认: 160 spm)
- `--max-cadence`: 最大步频 (默认: 180 spm)
- `--cadence-factor`: 步频调整系数 (默认: 2.0)

#### 功率参数
- `--power-factor`: 功率计算系数 (默认: 1.0)
- `--min-power`: 最小功率 (默认: 100 W)

#### 其他参数
- `--speed-threshold`: 运动速度阈值 (默认: 0.8 m/s)
- `--start-time`: 自定义开始时间 (ISO格式)
- `--activity-type`: 运动类型 (默认: Running)
- `--device-name`: 设备名称 (默认: GPX Converter)
- `--calories-per-km`: 每公里消耗卡路里 (默认: 60)

## 💡 使用示例

### 1. 基本转换
```bash
# 最简单的用法
python3 gpx_to_tcx.py morning_run.gpx -o morning_run.tcx
```

### 2. 自定义心率参数
```bash
# 适合年轻运动员的心率设置
python3 gpx_to_tcx.py route.gpx -o activity.tcx \
  --base-hr 110 --max-hr 190
```

### 3. 自定义开始时间
```bash
# 设置特定的运动开始时间
python3 gpx_to_tcx.py route.gpx -o activity.tcx \
  --start-time "2024-12-25T08:30:00Z"
```

### 4. 骑行运动设置
```bash
# 适合骑行的参数设置
python3 gpx_to_tcx.py bike_route.gpx -o bike_activity.tcx \
  --activity-type "Biking" \
  --base-cadence 80 --max-cadence 120 \
  --base-hr 100 --max-hr 160
```

### 5. 完全自定义
```bash
# 所有参数都自定义
python3 gpx_to_tcx.py route.gpx -o custom_activity.tcx \
  --base-hr 115 --max-hr 175 --hr-factor 1.2 \
  --base-cadence 165 --max-cadence 185 \
  --power-factor 1.1 --min-power 120 \
  --activity-type "Running" \
  --start-time "2024-12-25T08:30:00Z" \
  --calories-per-km 65 \
  --device-name "我的GPS手表"
```

## 📊 工具特点

### ✅ 自动生成的数据
- **距离计算**: 使用精确的Haversine公式计算GPS点间距离
- **速度分析**: 根据轨迹点时间差计算实时速度
- **心率模拟**: 基于速度和运动进程智能模拟心率变化
- **步频计算**: 根据速度自动调整步频数据
- **功率估算**: 基于速度和心率计算功率输出
- **卡路里消耗**: 根据距离和设定参数估算卡路里

### 🎯 智能算法
- **渐进式心率**: 模拟运动过程中心率的自然变化
- **速度阈值**: 低于阈值时自动调整各项指标
- **疲劳因子**: 随运动进行逐渐增加心率，更真实
- **数据平滑**: 避免数据突变，保持自然过渡

## 🔧 故障排除

### 常见问题

**Q: 提示"没有找到轨迹点"**
A: 检查GPX文件格式是否正确，确保包含`<trkpt>`标签

**Q: 生成的TCX文件很小**
A: 可能GPX文件中轨迹点较少，检查原始文件内容

**Q: 心率数据看起来不真实**
A: 调整`--base-hr`、`--max-hr`和`--hr-factor`参数

**Q: 上传到平台后显示异常**
A: 检查`--activity-type`是否设置正确，尝试不同的运动类型

### 调试技巧

1. **先测试工具**:
   ```bash
   python3 test_gpx_to_tcx.py
   ```

2. **使用示例文件**:
   ```bash
   python3 gpx_to_tcx.py example_route.gpx -o test.tcx
   ```

3. **检查输出信息**: 工具会显示详细的处理过程和统计信息

4. **验证TCX文件**: 可以用文本编辑器打开查看XML结构

## 📁 文件说明

- `gpx_to_tcx.py`: 主转换工具
- `test_gpx_to_tcx.py`: 测试脚本
- `example_route.gpx`: 示例GPX文件
- `GPX转TCX使用指南.md`: 本说明文档

## 🎉 成功案例

转换成功后，你会看到类似输出：
```
✅ 找到 31 个GPX轨迹点
📏 总距离: 420.42 米
⏱️  总时间: 30 秒
🏃 平均速度: 14.01 m/s
🔥 估算卡路里: 25 卡
✅ 转换完成！
🎉 成功！TCX文件已保存为: demo_activity.tcx
```

生成的TCX文件可以直接上传到：
- Garmin Connect
- Strava
- Training Peaks
- 其他支持TCX格式的运动平台

## 💪 进阶使用

### 批量转换
可以编写简单的脚本批量处理多个GPX文件：

```bash
#!/bin/bash
for gpx_file in *.gpx; do
    tcx_file="${gpx_file%.gpx}.tcx"
    python3 gpx_to_tcx.py "$gpx_file" -o "$tcx_file"
done
```

### 参数优化
根据不同运动类型调整参数：

- **跑步**: 默认参数即可
- **骑行**: 降低步频，调整心率范围
- **徒步**: 降低速度阈值和心率
- **游泳**: 需要特殊处理（本工具主要适用陆地运动）

---

**祝你使用愉快！如有问题，请检查参数设置或查看错误信息。** 🏃‍♂️💨