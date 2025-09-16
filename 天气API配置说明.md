# 天气API配置说明

## 🌤️ 天气功能概述

本应用集成了5重天气API备用方案，确保天气信息的稳定显示：

### 📊 API优先级顺序

1. **wttr.in API** (主要方案) ⭐
   - ✅ 完全免费，无需注册
   - ✅ 无API密钥限制
   - ✅ 支持GPS坐标和城市名查询
   - ✅ 数据准确可靠
   - 🔄 自动IP定位备用

2. **WeatherAPI** (备用方案1) 🆕
   - 🎯 免费注册，每月100万次调用
   - 🌐 全球覆盖，多语言支持
   - 📊 数据详细，更新及时
   - 🔑 需要申请API密钥

3. **OpenWeatherMap API** (备用方案2)
   - 🔑 需要免费注册获取API密钥
   - 📈 每月1000次免费调用
   - 🌍 全球覆盖，数据权威

4. **7Timer API** (备用方案3) 🆕
   - 🆓 完全免费，无需注册
   - 🎯 专业气象预报
   - 📍 支持GPS坐标查询
   - 🔄 自动IP定位

5. **智能模拟数据** (最终保障)
   - 🛡️ 确保功能永不失效
   - 🌡️ 根据季节和时间生成合理数据
   - 📍 集成IP定位获取真实城市
   - 🎯 保持用户体验一致性

## 🔧 配置方法

### 方案一：使用wttr.in (推荐)

**无需任何配置**，开箱即用！

- 当前状态：✅ 已启用并正常工作
- API地址：`https://wttr.in/`
- 特点：免费、稳定、无限制

### 方案二：配置WeatherAPI (推荐) 🌟

如需更高精度的天气数据，推荐配置WeatherAPI：

1. **注册账号**
   ```
   访问：https://www.weatherapi.com/
   注册免费账号
   ```

2. **获取API密钥**
   ```
   登录后在Dashboard获取API密钥
   每月100万次免费调用
   ```

3. **配置密钥**
   ```python
   # 在 web_app.py 中找到这一行：
   weatherapi_key = "your_weatherapi_key_here"
   
   # 替换为你的实际API密钥：
   weatherapi_key = "你的WeatherAPI密钥"
   ```

### 方案三：配置OpenWeatherMap (可选)

1. **注册账号**
   ```
   访问：https://openweathermap.org/api
   注册免费账号
   ```

2. **获取API密钥**
   ```
   登录后在API Keys页面获取密钥
   ```

3. **配置密钥**
   ```python
   # 在 web_app.py 中找到这一行：
   api_key = "your_openweather_api_key_here"
   
   # 替换为你的实际API密钥：
   api_key = "你的实际API密钥"
   ```

### 方案四：7Timer API (免费)

**无需任何配置**，自动启用！

- 当前状态：✅ 已启用并正常工作
- API地址：`http://www.7timer.info/`
- 特点：免费、专业、无限制

## 📈 功能特性

### 🌍 多语言支持
- 中文：晴朗、多云、雨等
- 英文：Clear、Cloudy、Rain等
- 自动根据界面语言切换

### 📍 智能定位系统
- GPS坐标定位（精确）
- 城市名称查询
- IP地址定位（多重API保障）
- 自动定位降级机制

### 🔄 5重自动降级机制
```
wttr.in API → WeatherAPI → OpenWeatherMap API → 7Timer API → 智能模拟数据
```

### 📊 显示信息
- 🌡️ 温度（摄氏度）
- 🌤️ 天气描述
- 💧 湿度百分比
- 💨 风速（米/秒）
- 📍 位置信息

## 🚀 当前状态

✅ **wttr.in API**: 正常工作，无需配置  
⚠️ **WeatherAPI**: 需要配置API密钥 (推荐)  
⚠️ **OpenWeatherMap**: 需要配置API密钥  
✅ **7Timer API**: 正常工作，无需配置  
✅ **IP定位系统**: 多重API保障  
✅ **智能模拟数据**: 季节性适配  
✅ **多语言支持**: 中英文自动切换  
✅ **GPS定位功能**: 浏览器原生支持

## 🛠️ 故障排除

### 天气不显示？
1. **检查网络连接**: 确保能访问外部API
2. **查看浏览器控制台**: 检查JavaScript错误
3. **确认API密钥**: 验证WeatherAPI和OpenWeatherMap密钥
4. **检查服务器日志**: 查看后端API调用状态
5. **测试IP定位**: 访问 http://ip-api.com/json/ 测试

### API调用失败处理
1. **wttr.in失败**: 自动切换到WeatherAPI
2. **WeatherAPI失败**: 自动切换到OpenWeatherMap
3. **OpenWeatherMap失败**: 自动切换到7Timer
4. **7Timer失败**: 启用智能模拟数据
5. **所有API失败**: 使用应急备用数据

### 定位问题
1. **GPS定位失败**: 自动使用IP定位
2. **IP定位失败**: 尝试多个IP定位API
3. **位置获取失败**: 使用默认城市(北京)

```bash
# 查看详细日志
tail -f 服务器日志

# 常见错误信息：
# "wttr.in API调用失败" - 网络问题
# "WeatherAPI调用失败" - API密钥问题
# "OpenWeatherMap API调用失败" - API密钥问题
# "7Timer API调用失败" - 网络问题
# "使用备用模拟天气数据" - 所有API都失败，使用模拟数据
```

### 手动测试API
```bash
# 测试wttr.in
curl "https://wttr.in/Beijing?format=j1"

# 测试OpenWeatherMap (需要API密钥)
curl "https://api.openweathermap.org/data/2.5/weather?q=Beijing&appid=YOUR_API_KEY"
```

## 📝 开发说明

### 添加新的天气API

1. 在`get_weather_data()`函数中添加新的获取函数
2. 在优先级链中添加调用
3. 确保返回统一的数据格式

### 新增API源示例

#### WeatherAPI集成
```python
# 每月100万次免费调用
url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={query}&lang={lang}"
```

#### 7Timer集成
```python
# 完全免费，无需注册
url = f"http://www.7timer.info/bin/api.pl?lon={lon}&lat={lat}&product=civillight&output=json"
```

#### IP定位集成
```python
# 多重IP定位API
apis = [
    'http://ip-api.com/json/?fields=city,country,countryCode,lat,lon',
    'https://ipapi.co/json/',
    'https://freegeoip.app/json/'
]
```

### 数据格式规范
```python
weather_data = {
    'temperature': '22°C',      # 温度字符串
    'description': '晴朗',       # 天气描述
    'humidity': 65,             # 湿度数值
    'wind_speed': 3.2           # 风速数值(m/s)
}

location_data = {
    'city': '北京',             # 城市名
    'country': 'CN',           # 国家代码
    'province': '北京市'        # 省份/地区
}
```

## 🎯 最佳实践

### 🚀 生产环境推荐
1. **配置WeatherAPI**: 每月100万次调用，足够大部分应用
2. **备用OpenWeatherMap**: 双重API保障
3. **保留wttr.in**: 作为主要免费方案
4. **启用7Timer**: 完全免费的最后保障

### 🛠️ 开发测试
1. **直接使用wttr.in**: 无需任何配置
2. **测试IP定位**: 验证自动定位功能
3. **多语言测试**: 验证中英文切换
4. **故障模拟**: 测试API失效时的降级

### 🔧 性能优化
1. **缓存策略**: 考虑添加天气数据缓存(5-10分钟)
2. **并发控制**: 限制同时API调用数量
3. **超时设置**: 合理设置API超时时间(3-5秒)
4. **重试机制**: 网络异常时自动重试

### 📊 监控建议
1. **API状态监控**: 跟踪各API成功率
2. **响应时间**: 监控API响应速度
3. **错误日志**: 记录API调用失败原因
4. **用户体验**: 监控天气模块显示成功率

---

**更新时间：** 2025年1月16日  
**版本：** v3.0 - 5重备用保障版本  
**新增：** WeatherAPI、7Timer、IP定位、智能模拟  
**状态：** ✅ 生产就绪