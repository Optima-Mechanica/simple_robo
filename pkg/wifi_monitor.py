import logging


def check_wf_adapter(line: str) -> bool:
    wf_names = ['wlan', 'ath', 'wlo']
    for wf_name in wf_names:
        if wf_name in line:
            return True

    return False


def get_wifi_signal_strength() -> int | None:
    """
    Reads the Wi-Fi signal strength from /proc/net/wireless.
    Returns the signal strength in dBm as an integer, or None if an error occurs.
    """
    try:
        with open('/proc/net/wireless', 'r') as wf_devs:
            lines = wf_devs.readlines()
            header = {i: n.lower() for i, n in enumerate(lines[1].split('|'))}

            link_field_num = [i for i, n in header.items() if 'level' in n][0]
            level_field_num = [i for i, n in header.items() if 'link' in n][0]

            # Skip header lines.
            for line in lines[2:]:
                # Check for typical interface names.
                if check_wf_adapter(line):
                    parts = line.strip().split()
                    if len(parts) > max(link_field_num, level_field_num):
                        # Example format: interface | status | quality/max | level(dBm) | noise | ...
                        try:
                            # Try getting the signal level directly.
                            signal_level_dbm = int(float(parts[link_field_num]))
                            return signal_level_dbm
                        except ValueError:
                            # If not an int, try parsing quality percentage.
                            quality_str = parts[level_field_num]
                            if '/' in quality_str:
                                quality, max_quality = map(int, quality_str.split('/'))
                                # Approximate conversion to dBm if needed (less accurate)
                                return (quality / max_quality) * 100
                            else:
                                return int(float(quality_str))
    except IOError as e:
        logging.error('Error reading /proc/net/wireless: %s', e)

    return None
