# PARETO_CURVE - Generate the model, perform verification to obtain
# the appropriate multi-objective synthesis problem and 
# perform synthesis to obtain the pareto curve desired.

# Author: Francisco Girbal Eiras, MSc Computer Science
# University of Oxford, Department of Computer Science
# Email: francisco.eiras@cs.ox.ac.uk
# 9-Jun-2018; Last revision: 9-Jun-2018

import sys, os, subprocess, csv, argparse
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib import cm
from datetime import datetime
startTime = datetime.now()

plt.rc('text', usetex=True)
plt.rc('font', family='serif')
plt.rc('font', size=13)

parser=argparse.ArgumentParser(
    description='''Generate the model, perform verification to obtain the appropriate multi-objective synthesis problem and perform synthesis to obtain the pareto curve desired.''')
parser.add_argument('[v]', type=int, default=29, help='Initial velocity of the vehicle.')
parser.add_argument('[v1]', type=int, default=30, help='Initial velocity of the other vehicle.')
parser.add_argument('[x1_0]', type=int, default=15, help='Initial position of the other vehicle.')
parser.add_argument('--clean [VALUE]', type=str, help='If [VALUE] = False, then generated files (model and individual results) will be maintained (default = True).')
parser.add_argument('--path [PATH]', type=str, help='Generated file will be saved in PATH.')
args=parser.parse_args()

res = []

v = sys.argv[1]
v1 = sys.argv[2]
x1_0 = sys.argv[3]
properties_file = "properties/verification.pctl"
path = "results"

if len(sys.argv) > 4 and sys.argv[4] == "--clean" and sys.argv[5] == "False":
	cleaning_up = False
else:
	cleaning_up = True

if len(sys.argv) > 4 and sys.argv[4] == "--path":
	path = sys.argv[6]

def obtain_curve():
	# Construct the file
	print('Generating the model...')
	os.system('python3 model/mdp_generator.py model/model_tables/control_table.csv model/model_tables/acc_table.csv %s %s %s > /dev/null'%(v,v1,x1_0))

	# ------------- Verification -------------
	print('Building the model and performing verification...')
	proc = subprocess.Popen('storm --prism mdp_model.pm --prop properties/verification.pctl', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	output = str(proc.stdout.read())

	idx = output.find('\\n-------------------------------------------------------------- \\n', 500)
	output = output[idx + 69:]
	idx3 = 0

	Tmin = 30

	while idx3 != -1:
		idx1 = output.find('\\n')
		first_line = output[0:idx1]
		idx2 = output.find('\\n', idx1+1)
		second_line = output[idx1+2:idx2+2]
		idx3 = output.find('\\n\\n', idx2+1)

		prop = first_line[24:first_line.find('...')-1]
		val = second_line[29:second_line.find('\\n')]

		try:
			probability = float(val)
		except ValueError:
			print('----------------------------------\n\n')
			print(output)
			exit()

		res.append([prop, probability])
		
		print(prop + ' : ' + str(probability))
		if 'Pmax=? [F ((x = 500) & (t <' in prop and probability != 0:
			T = int(prop[28:30])
			Tmin = min(T, Tmin)
		output = output[idx3+4:]

	# ------------- Synthesis -------------
	multi_obj_query = "multi(Pmin=? [F crashed], Pmax=? [F (x=length) & (t<%d)])"%Tmin
	print('Synthesis using the query "%s"'%multi_obj_query)

	os.system("mkdir results/r_%s_%s_%s > /dev/null"%(v,v1,x1_0))

	proc = subprocess.Popen('storm --prism mdp_model.pm --prop "%s" --multiobjective:precision 0.01 --multiobjective:exportplot results/r_%s_%s_%s'%(multi_obj_query,v,v1,x1_0), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	output = str(proc.stdout.read())
	return Tmin

def draw_curve(Tmin):
	x = []
	y = []

	with open("results/r_%s_%s_%s/paretopoints.csv"%(v,v1,x1_0)) as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			x.append(float(row["x"]))
			y.append(float(row["y"]))

	new_x, new_y = zip(*sorted(zip(x, y)))
	new_x = [xs for xs in new_x]
	new_y = [ys for ys in new_y]

	fig, ax = plt.subplots()

	plt.plot(new_x, new_y, marker = 'o')

	new_x.append(max(x))
	new_y.append(0)

	new_x.append(min(x))
	new_y.append(0)

	xy = np.vstack((new_x, new_y)).T

	polygon = [Polygon(xy, True)]
	p = PatchCollection(polygon, alpha=0.3)
	p.set_color("g")

	ax.add_collection(p)

	plt.xlabel('P$_{min=?}$ [F crashed]')
	plt.ylabel('P$_{max=?}$ [F ((x = 500) \& (t $<$ %s))]'%Tmin)

	plt.show()


Tmin = obtain_curve()
draw_curve(Tmin)
print('Done.')
# print(datetime.now() - startTime)






