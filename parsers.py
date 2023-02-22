#!/usr/bin/env python3

'''
A library of functions for parsing network device command output.
'''


def f5_convert_config_to_json(output):
    '''
    Converts the F5 CLI output to JSON. This function needs further testing. I
    have tested it with some F5 VIPs and it works.

    TODO: Test on pools, nodes, and other config items.
    TODO: Add comments.

    Args:
        output (str):   A single config element. For example, if parsing the
                        output of 'tmsh list ltm virtual', then 'output' would
                        start with the line 'ltm virtual vipName {' and end
                        with the final '}'

    Returns:
        output (dict):  A dictionary containing the converted output.
    '''
    formatted = ['{']

    num_closers = 0

    counter = 0
    for line in output:
        if len(line.split()) == 2:
            if '{' in line:
                line = f'"{line.split()[0]}": ' + '{'
                formatted.append(line)
            else:
                # print(line)
                line = f'"{line.split()[0]}": ' + f'"{line.split()[1]}"'
                try:
                    next_line = output[counter+1]
                    if len(next_line.split()) == 1 and '}' in next_line:
                        pass
                    else:
                        line = line + ','
                    formatted.append(line)
                except Exception:
                    # This exception will be caught if 'next' exceeds the
                    # length of the list. If that happens, it will mean that
                    # 'line' is the last item in 'output'. Therefore, we will
                    # need to add a closing bracker + comma after appending the
                    # line.
                    formatted.append(line)
                    formatted.append('},')
        if len(line.split()) > 2:
            if '{' in line and '}' in line:
                line = f'"{line.split()[0]}": ' + '{}'
                next_line = output[counter+1]
                if len(next_line.split()) == 1 and '}' in next_line:
                    pass
                else:
                    line = line + ','
                formatted.append(line)
            elif '{' in line:
                for item in line.split()[:-1]:
                    item = f'"{item}": ' + '{'
                    formatted.append(item)
                    num_closers += 1
        if len(line.split()) == 1 and '}' in line:
            try:
                line = f'{line.split()[0]}'
                next_line = output[counter+1]
                if len(next_line.split()) == 1 and '}' in next_line:
                    pass
                else:
                    line = line + ','
            except Exception:
                line = f'{line.split()[0]},'
            formatted.append(line)
        elif len(line.split()) == 1:
            line = line.split()[0]
            line = f'"{line}": ' + '{}'
            print(counter, output[0], output[counter])#, line)
            print(counter+1)
            next_line = output[counter+1]
            if len(next_line.split()) == 1 and '}' in next_line:
                pass
            else:
                line = line + ','
            formatted.append(line)
        counter += 1
    formatted[-1] = formatted[-1].strip(',')
    for item in range(1, num_closers+1):
        formatted.append('}')
    formatted = '\n'.join(formatted)
    output = formatted
    return output


# config = config[8980:10894]
# vip_configs = list()

# pos = 0
# for line in config:
#     if line[:3] == 'ltm':
#         vip_config = list()
#         pos = config.index(line)
#         while config[pos][:2] != '}\n':
#             vip_config.append(config[pos])
#             pos += 1
#         vip_configs.append(vip_config)
#     pos += 1


# text = [_.strip() for _ in vip_configs]
# pprint(text)


# import json
# import importlib
# import parsers as pa
# import re
# from pprint import pprint

# conf_file = "/Users/jspiers/Documents/Projects/Hennepin Healthcare/Archives/2022-05-31/scf_F5-DMZ-2_2022-05-31_15-48.scf"
# with open(conf_file, 'r') as f:
#     config = f.readlines()

# pattern = '^ltm virtual\\b '

# vip_configs = list()
# for line in config:
#     result = re.search(pattern, line)
#     if result:
#         vip_config = [line]
#         next = config.index(line) + 1
#         while config[next][0] != '}':
#             vip_config.append(config[next])
#             next += 1
#         vip_configs.append(vip_config)
