#!/usr/bin/env python3

import argparse
import re

def main():
	parser = argparse.ArgumentParser(description='Process DTSI file to extract OCV capacity tables.')
	parser.add_argument('-i', '--input', required=True, help='Input DTSI file')
	parser.add_argument('-o', '--output', required=True, help='Output text file')
	args = parser.parse_args()

	# Read the input DTSI file
	with open(args.input, 'r') as f:
		lines = f.readlines()

	# Variables to store the node content
	in_node = False
	brace_count = 0
	node_lines = []

	# Extract the qcom,pc-temp-v2-lut node
	for line in lines:
		line = line.strip()
		if not in_node:
			if line.startswith('qcom,pc-temp-v2-lut'):
				if '{' in line:
					in_node = True
					brace_count = line.count('{') - line.count('}')
					node_lines.append(line)
				else:
					# The '{' is in the next line
					in_node = True
					brace_count = 0
		else:
			brace_count += line.count('{') - line.count('}')
			node_lines.append(line)
			if brace_count == 0:
				in_node = False
				break  # Assuming only one node to process

	if not node_lines:
		print('Error: qcom,pc-temp-v2-lut node not found in the input file.')
		return

	# Join the node lines into a single string
	node_content = ' '.join(node_lines)

	# Extract qcom,lut-col-legend values
	col_legend_match = re.search(r'qcom,lut-col-legend\s*=\s*<([^;]+)>;', node_content)
	if col_legend_match:
		col_legend_str = col_legend_match.group(1)
		col_legend_values = col_legend_str.strip().split()
	else:
		print('Error: qcom,lut-col-legend not found')
		return

	# Extract qcom,lut-data values
	data_match = re.search(r'qcom,lut-data\s*=\s*(.+?);', node_content, re.DOTALL)
	if data_match:
		data_str = data_match.group(1)
		# Find all data entries enclosed in '<...>'
		data_values = re.findall(r'<([^>]+)>', data_str)
		data_list = []
		for dv in data_values:
			nums = dv.strip().split()
			data_list.append([int(num) for num in nums])
	else:
		print('Error: qcom,lut-data not found')
		return

	# Transpose the data to get columns
	data_columns = list(zip(*data_list))

	# Generate capacity percentages
	percentages = list(range(100, 9, -2)) + list(range(9, -1, -1))

	# Check if the data length matches the percentages length
	if any(len(col) != len(percentages) for col in data_columns):
		print('Error: Data length does not match the number of capacity percentages.')
		return

	# Write the output file
	with open(args.output, 'w') as f_out:
		# Write the ocv-capacity-celsius line
		f_out.write('\t\tocv-capacity-celsius = <')
		f_out.write(' '.join(col_legend_values))
		f_out.write('>;\n')

		# Write the ocv-capacity-table-N lines
		for idx, col in enumerate(data_columns):
			f_out.write('\t\tocv-capacity-table-{} = '.format(idx))
			pairs = []
			for value, percentage in zip(col, percentages):
				value_scaled = value * 100
				pair_str = '<{} {}>'.format(value_scaled, percentage)
				pairs.append(pair_str)
			# Format the pairs, 6 per line
			pair_lines = [', '.join(pairs[i:i+6]) for i in range(0, len(pairs), 6)]
			for i, pline in enumerate(pair_lines):
				if i == 0:
					f_out.write(pline + ',\n')
				elif i == len(pair_lines) - 1:
					# Last line ends with a semicolon
					f_out.write('\t\t\t	   ' + pline + ';\n')
				else:
					f_out.write('\t\t\t	   ' + pline + ',\n')

if __name__ == '__main__':
	main()

