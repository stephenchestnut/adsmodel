# Copyright 2013, all rights reserved.
# Stephen Chestnut and Rico Zenklusen
# Johns Hopkins University

# list of functions
#
# tabular(A,spec='',hline=False): print the 2-d list A to a string as a latex tabular
# tabular_rows(A,hline=False): print the 2-d list A to a string as rows in a latex tabular
# tabular_caps(spec=''): return the latex code to start and finish a tabular as strings
# table(A,spec=''): print the 2-d list A to a string as a latex table
# table_caps(): print the latex code to start and finish a table as strings

import pdb
import copy

def tabular_caps(spec=''):    
    top = '\\begin{tabular}{' + spec + '}\n'
    bot = '\n\\end{tabular}'
    return top,bot

def tabular_rows(A,hline=False):
    eol = '\\\\\n'
    bol = ''
    if hline:
        bol = '\\hline '

    ret = _tabular_row(A[0])
    for x in A[1:]:
        ret += eol
        ret += bol + _tabular_row(x)
    return ret

def _tabular_row(x):

    ret = ''
    ret += texstr(x[0])
    for y in x[1:]:
        ret += ' & ' + texstr(y)
    return ret
    
def tabular(A,spec='',hline=False):
    if spec=='':
        spec = 'c'*len(A[0])
    top,bot = tabular_caps(spec)
    mid = tabular_rows(A,hline)
    return top + mid + bot

def table_caps(sizestr=''):
    if sizestr!='':
        sizestr += '\n'
    return '\\begin{table}\n'+sizestr,'\n\\end{table}'

def sidewaystable_caps( sizestr=''):
    if sizestr!='':
        sizestr += '\n'
    return '\\begin{sidewaystable}\n'+sizestr,'\n\\end{sidewaystable}'

def sideways_headers(A,start=1):
    #given a table A with headers in the first row, 
    # return a shallow copy of A with \begin{sideways}--\end{sideways} in each header 
    # starting with the column start

    B=copy.copy(A)
    for ii in range(start,len(B[0])):
        B[0][ii] = '\\begin{sideways}' + B[0][ii] + '\\end{sideways}'

    return B

def table(A,spec='',hline=False,label='',caption=''):
    top,bot = table_caps()
    mid = tabular(A,spec,hline)
    return top + float_label_caption(label,caption) + mid + bot

def float_label_caption(label,caption):
    ret=''
    if len(label)>0:
        ret += '\\label{' + label + '}\n'
    if len(caption)>0:
        ret += '\\caption{' + caption + '}\n'
    return ret

def figure_caps(fig_opt='',label='',caption=''):
    top = '\\begin{figure}['+fig_opt+']\n' 
    top += float_label_caption(label,caption)
    top += '\\begin{center}\n'
    bot = '\\end{center}\n\\end{figure}'
    return top,bot

def texstr(x):
    #create a string that is ok for tex
    s = str(x)
    s=s.replace('&','\&')
    return s

def tikzpicture_caps(args=['']):
    #create the tikzpicture opener and closer with given list of arguments (as list of strings)
    arg = '[' + _string_list_to_csv_string(args) + ']'
    return '\\begin{tikzpicture}' + arg, '\\end{tikzpicture}'

def tikz_drawfill_plot(x,y,color='black!30',plot_opts=['']):

    ret = '\\filldraw[' + color + '] ' + tikz_plot(x,y,plot_opts) + ';'
    return ret

def tikz_plot(x,y,plot_opts=['']):
    arg = '[' + _string_list_to_csv_string(plot_opts) + ']'
    ret = 'plot' + arg + ' coordinates{'
    for pt in zip(x,y):
        ret+=str(pt)
    ret += '}'
    return ret

    
def tikz_segmented_fill_plot(x,Y,color='blue',plot_opts=['']):
    #create a segmented plot of the data in the rows of Y.  There will be a line
    # plot with the area under it filled proportionally according to the values 
    # in the rows of Y.  The segments are ordered top to bottom the same as the rows
    # of y.  The values in the single list x should contain the (common) x coordinates 
    # of the data in Y (i.e. len(x) = len(Y[0])

    Yc = copy.copy(Y)
    m = len(Yc)
    n = len(Yc[0])
    x= [x[0]] + x + [x[-1]]
    for ii in range(m-2,-1,-1): #may Yc a cumulative version of Y and plot each row
        for jj in range(n):
            Yc[ii][jj] += Yc[ii+1][jj]

    this_color = color + '!' + str(70)
    ret = tikz_drawfill_plot(x, [0] + Yc[0] + [0],this_color,plot_opts)
    for ii in range(1,m):
        this_color = color + '!' + str(70*(m-ii)/m)
        ret += '\n' + tikz_drawfill_plot(x,[0] + Yc[ii] +[0],this_color,plot_opts)

    return ret
    
def pgf_addplot_coordinates(x,y,plot_opts=[''],closed=False):
    if plot_opts==['']:
        ret = '\\addplot coordinates {'
    else:
        ret = '\\addplot ' + '[' + _string_list_to_csv_string(plot_opts) + '] coordinates {'
    for pt in zip(x,y):
        ret += str(pt) +'\n'
    ret += '}'
    if closed:
        ret += '\\closedcycle'
    ret += ';'
    return ret

def pgf_axis_caps(axis_opts=['']):
    top='\\begin{axis}[' + _string_list_to_csv_string(axis_opts) + ']\n'
    return top,'\\end{axis}'

def pgf_stacked_area_plot(x,Y,legend=[],yrange=[],axis_opts=['']):
    axis_opts += ['stack plots=y','area style']
    if yrange!=[]:
        axis_opts += ['ymin='+str(yrange[0]),'ymax='+str(yrange[1])]
    top,bot = pgf_axis_caps(axis_opts)
    ret = pgf_addplot_coordinates(x, Y[0],[''],True)
    for ii in range(1,len(Y)):
        #this_color = color + '!' + str(70*(m-ii)/m)
        ret += '\n' + pgf_addplot_coordinates(x,Y[ii],[''],True)

    if legend != []:
        ret += '\\legend{' + _string_list_to_csv_string(legend) + '}\n'
    return top + ret + bot


def _string_list_to_csv_string(x):
    #convert a list of strings into a comma separated string
    ret = x[0]
    for s in x[1:]:
        ret += ','+s
    return ret
    

    
