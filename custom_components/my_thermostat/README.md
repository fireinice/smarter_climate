# My Thermostat Home Assistant Integration

## 概述

这是一个用于 Home Assistant 的自定义集成，旨在根据您的温度和湿度传感器读数自动控制现有的气候实体。它允许您设置目标温度和目标湿度，并根据这些值智能地调整气候设备的运行模式（制冷、制热、除湿）。

## 主要功能

*   **集成现有实体**: 不创建新的气候或传感器实体，而是接收 Home Assistant 中已存在的气候实体、温度传感器实体和湿度传感器实体的 `entity_id`。
*   **智能温度控制**: 
    *   如果当前温度高于目标温度 2.0°C 以上，气候模式将切换为 `cool`（制冷），并将目标温度设置为配置的目标温度。
    *   如果当前温度低于目标温度 2.0°C 以上，气候模式将切换为 `heat`（制热），并将目标温度设置为配置的目标温度。
*   **智能湿度控制**:
    *   如果当前湿度高于目标湿度 10% 以上（且不满足温度条件），气候模式将切换为 `dry`（除湿）。
*   **默认行为**: 如果以上温度和湿度条件均不满足，气候模式将默认设置为 `cool`（制冷），并将温度设置为配置的目标温度。

## HACS 安装

1.  **添加自定义仓库**: 在 Home Assistant 前端，导航到 HACS -> 集成 -> 右上角三个点 -> `Custom repositories`。
2.  **URL**: 粘贴此集成的 GitHub 仓库 URL（假设您会将其上传到 GitHub）。
    *   **类别**: 选择 `Integration`。
    *   点击 `ADD`。
3.  **搜索并安装**: 在 HACS 中搜索 "My Thermostat Integration"，然后点击 `INSTALL`。
4.  **重启 Home Assistant**: 安装完成后，请务必重启 Home Assistant 服务以加载新的集成。

## 配置

将以下配置添加到您的 Home Assistant `configuration.yaml` 文件中：

```yaml
# configuration.yaml
my_thermostat:
  climate_entity_id: "climate.your_existing_thermostat" # 必需：替换为您在 Home Assistant 中现有的气候实体ID
  temperature_sensor_id: "sensor.your_existing_temperature_sensor" # 必需：替换为您在 Home Assistant 中现有的温度传感器ID
  humidity_sensor_id: "sensor.your_existing_humidity_sensor" # 必需：替换为您在 Home Assistant 中现有的湿度传感器ID
  target_temperature: 22.0 # 可选：您希望保持的温度目标值，默认为 22.0°C
  target_humidity: 50.0 # 可选：您希望保持的湿度目标值，默认为 50.0%
```

替换示例中的 `entity_id` 为您实际的实体ID。 