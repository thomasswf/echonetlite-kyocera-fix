# 0x027D 蓄電池 (Storage Battery)
# Kyocera (Enerezza Plus)
# https://echonet.jp/introduce/gz-001033/

from homeassistant.const import CONF_NAME, CONF_ICON, CONF_SERVICE
from pychonet.lib.epc_functions import _int


def _raw_int(edt, _options=None):
    """Decode an undocumented property as a raw unsigned integer.

    pychonet calls EPC functions as func(edt, options), so the options
    argument must be accepted even when unused.
    """
    return int.from_bytes(edt, "big", signed=False)

# Empirically calibrated on a real Enerezza Plus unit (2026-11-23),
# verified against raw ECHONET Lite packets (EPC 0xF0 EDT values):
# 0x01: "Auto-Sell (売電モード)"    - confirmed from raw packet capture
# 0x02: "Auto-Green (グリーンモード)" - confirmed from remote display + packets
#        (FullGreen also reports 0x02; it is not distinguishable via 0xF0)
# 0x05: "Standby (待機)"            - confirmed: the unit halts in this mode
# Force Charge acts via the standard operation mode (EPC 0xDA = charging).
# The previous mapping (0x02 Standby / 0x04 Sell / 0x05 Green / 0x07
# FullGreen / 0x08 Charge / 0x09 Discharge) was incorrect: selecting
# "Green Mode" (0x05) actually put the unit into standby.

QUIRKS = {
    0xF0: { # Kyocera Special Operation mode setting
        "EPC_FUNCTION": [
            _int,
            {
                0x01: "Sell Mode",
                0x02: "Green Mode",
                0x05: "Standby",
            },
        ],
        "ENL_OP_CODE": {
            CONF_NAME: "Special Operation mode setting",
            CONF_ICON: "mdi:format-list-bulleted",
        },
    },
    # Undocumented user-defined properties, confirmed present on a real
    # Enerezza Plus via its self-declared property maps (2026-11-26):
    # Get map (0x9F) includes 0xF0-0xF3; Set map (0x9E) includes 0xF0-0xF3;
    # status-change announcement map (0x9D) includes 0xF1 and 0xF2.
    # Exposed as raw integer sensors for calibration (are any of these the
    # Green vs Full Green distinction that 0xF0 cannot express?).
    0xF1: { # Kyocera user-defined property 2 (undocumented)
        "EPC_FUNCTION": [_raw_int, None],
        "ENL_OP_CODE": {
            CONF_NAME: "User property 0xF1",
            CONF_ICON: "mdi:help-circle-outline",
        },
    },
    0xF2: { # Kyocera user-defined property 3 (undocumented)
        "EPC_FUNCTION": [_raw_int, None],
        "ENL_OP_CODE": {
            CONF_NAME: "User property 0xF2",
            CONF_ICON: "mdi:help-circle-outline",
        },
    },
    0xF3: { # Kyocera user-defined property 4: charge/discharge time windows
        # Calibrated 2026-11-26 against the unit's remote display:
        # EDT = [charge start H, M, charge end H, M,
        #        discharge start H, M, discharge end H, M]
        # Green Mode:     11:00-13:00 / 13:01-10:59
        # Full Green:     charge disabled (12:58-12:59) / 13:00-12:57
        # i.e. Full Green is Green with the grid-charge window removed;
        # this property is where the mode difference actually lives.
        "EPC_FUNCTION": [_raw_int, None],
        "ENL_OP_CODE": {
            CONF_NAME: "User property 0xF3",
            CONF_ICON: "mdi:help-circle-outline",
            CONF_SERVICE: ["set_value_int_8b"],
        },
    },
}
