def generate_map():
    from collections import defaultdict
    from Dashboard.models import DistrictLog

    # 1. Fetch data
    logs = DistrictLog.objects.all().order_by('state', 'district')
    
    # 2. Group by state
    output_map = defaultdict(list)
    for log in logs:
        output_map[log.state].append(log.district)

    # 3. Print exactly formatted
    print("DATA_MAP = {")
    for state, districts in output_map.items():
        print(f"    '{state}': {districts},")
    print("}")

# Run it
generate_map()