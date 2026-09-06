import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import climate
from esphome.const import CONF_ID, CONF_NAME

from . import WavinAHC9000, WavinZoneClimate

CONF_PARENT_ID = "wavin_ahc9000_id"
CONF_CHANNEL = "channel"
CONF_MEMBERS = "members"


CONF_STRICT_MODE_WRITES = "strict_mode_writes"

CONF_USE_FLOOR_TEMPERATURE = "use_floor_temperature"

CONFIG_SCHEMA = climate.climate_schema(WavinZoneClimate).extend(
    {
        cv.GenerateID(CONF_PARENT_ID): cv.use_id(WavinAHC9000),
        cv.Optional(CONF_CHANNEL): cv.int_range(min=1, max=16),
        cv.Optional(CONF_MEMBERS): cv.ensure_list(cv.int_range(min=1, max=16)),
        cv.Optional(CONF_STRICT_MODE_WRITES, default=False): cv.boolean,
        cv.Optional(CONF_USE_FLOOR_TEMPERATURE, default=False): cv.boolean,
    }
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_PARENT_ID])
    var = cg.new_Pvariable(config[CONF_ID])
    await climate.register_climate(var, config)

    # Comfort climates expose the controller's floor minimum/maximum as a
    # two-point target. Do not use the *current* floor limits as the visual
    # limits in Home Assistant, otherwise a controller currently configured
    # for 22..27 C becomes impossible to adjust outside that range.
    #
    # The current C++ write path clamps floor-limit writes to 5..35 C. Use a
    # conservative 6..35 C UI range here so lower comfort limits can be
    # selected while keeping the UI within the component's supported write
    # range. ESPHome applies these overrides after WavinZoneClimate::traits().
    if config[CONF_USE_FLOOR_TEMPERATURE]:
        cg.add_define("USE_CLIMATE_VISUAL_OVERRIDES")
        cg.add(var.set_visual_min_temperature_override(6.0))
        cg.add(var.set_visual_max_temperature_override(35.0))
        cg.add(var.set_visual_temperature_step_override(0.5, 0.5))

    # Bind to hub
    cg.add(var.set_parent(hub))
    if CONF_CHANNEL in config:
        cg.add(var.set_single_channel(config[CONF_CHANNEL]))
        cg.add(hub.add_active_channel(config[CONF_CHANNEL]))
        if config[CONF_STRICT_MODE_WRITES]:
            cg.add(hub.set_strict_mode_write(config[CONF_CHANNEL], True))
        if config[CONF_USE_FLOOR_TEMPERATURE]:
            cg.add(var.set_use_floor_temperature(True))
        cg.add(hub.add_channel_climate(var))
    if CONF_MEMBERS in config:
        cg.add(var.set_members(config[CONF_MEMBERS]))
        for ch in config[CONF_MEMBERS]:
            cg.add(hub.add_active_channel(ch))
        cg.add(hub.add_group_climate(var))
