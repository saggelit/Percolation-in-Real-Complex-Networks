import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import collections
import matplotlib.ticker as ticker
from tqdm.notebook import  tqdm
import json


##### DATA #####

##### EP_Cit_Counts #####

EP_Cit_Counts=pd.read_table('201609_EP_Cit_Counts.txt',sep='|')

# Δημιουργία 2D λίστας με σπασμένες ημερομηνίες [YYYYMMDD] σε ξεχωριστές στήλες και EP_Pub_nbr
list_EP_Cit_Counts=list(map(list,zip(list(EP_Cit_Counts['EP_Pub_date']),list(EP_Cit_Counts['EP_Pub_nbr']))))
All_Dates=[]
for i in range(len(list_EP_Cit_Counts)):
    All_Dates.append([str(list_EP_Cit_Counts[i][0])[0:4],str(list_EP_Cit_Counts[i][0])[4:6],str(list_EP_Cit_Counts[i][0])[6:8],\
                      list_EP_Cit_Counts[i][1],str(list_EP_Cit_Counts[i][0])])


list_EP_Cit_Counts=All_Dates #2D List με ημερομηνίες σπασμένες και EP_Pub_nbr

# Αφαίρεση λανθασμένων καταχωρήσεων, διπλότυπων Pub_nbr και ταξινόμηση ως προς το Date
indexes=[]
for i in range (len(list_EP_Cit_Counts)):
    if list_EP_Cit_Counts[i][0]=='9999' or len(list_EP_Cit_Counts[i][3])!=9:
        indexes.append(i)
indexes.sort(reverse=True)
for i in indexes:
    del list_EP_Cit_Counts[i]

test_list_EP_Cit_Counts=[list(t) for t in set(tuple(element) for element in list_EP_Cit_Counts)]
list_EP_Cit_Counts=sorted(test_list_EP_Cit_Counts,key=lambda l:l[4])


##### EPO_App_reg #####
EPO_App_reg=pd.read_table('201602_EPO_App_reg.txt',sep='|')
EPO_App_reg=EPO_App_reg.sort_values(by=['Pub_nbr'],ignore_index=True)


##### EPO_Ipc #####
EPO_Ipc=pd.read_table('201602_EPO_IPC.txt',sep='|')
EPO_Ipc=EPO_Ipc.sort_values(by=['Appln_id'],ignore_index=True)

# Ταξινόμηση ευρεσιτεχνιών με βάση την κατηγορία τους
list_Ipc=list(map(list,zip(list(EPO_Ipc['Appln_id']),list(EPO_Ipc['IPC']))))
list_Ipc_A=[c for c in list_Ipc if str(c[1])[0]=='A']
list_Ipc_B=[c for c in list_Ipc if str(c[1])[0]=='B']
list_Ipc_C=[c for c in list_Ipc if str(c[1])[0]=='C']
list_Ipc_D=[c for c in list_Ipc if str(c[1])[0]=='D']
list_Ipc_E=[c for c in list_Ipc if str(c[1])[0]=='E']
list_Ipc_F=[c for c in list_Ipc if str(c[1])[0]=='F']
list_Ipc_G=[c for c in list_Ipc if str(c[1])[0]=='G']
list_Ipc_H=[c for c in list_Ipc if str(c[1])[0]=='H']


##### EPO_Inv_reg #####
EPO_Inv_reg=pd.read_table('201602_EPO_Inv_reg.txt',sep='|')
EPO_Inv_reg=EPO_Inv_reg.sort_values(by=['Pub_nbr'],ignore_index=True)


##### TIME WINDOWS #####

# Συνάρτηση για να παίρνει συγκεκριμένη στήλη από 2D list ως key για σορτάρισμα
def takeThirdColumn(elem):
    return elem[3]

def time_window_fun(list_EP_Cit_Counts,start_date,end_date):
    time_window=[]
    for i in range(len(list_EP_Cit_Counts)):
        if int(list_EP_Cit_Counts[i][0])>=int(start_date) and int(list_EP_Cit_Counts[i][0])<=int(end_date):
            time_window.append(list_EP_Cit_Counts[i])
    time_window.sort(key=takeThirdColumn)
    return time_window

# Δημιουργία χρονικών παραθύρων ταξινομημένα ως προς το Pub_nbr
All_time_windows=[]
for i in range(int(list_EP_Cit_Counts[0][0]),int(list_EP_Cit_Counts[-1][0])-2):
    start_date=i
    end_date=i+3 # +3 για τα 4 χρόνια διαφορά
    All_time_windows.append(time_window_fun(list_EP_Cit_Counts,start_date,end_date))


##### FUNCTIONS #####

##### Συναρτήσεις για εξαγωγή δεδομένων για κάθε TW

# Συνάρτηση για να παίρνει συγκεκριμένη στήλη από 2D list
def takeZeroColumn(elem):
    return elem[0]
def takeSecondColumn(elem):
    return elem[2]

# Συνάρτηση για περιορισμό δεδομένων εντός του εύρους των TW
# Κριτήριο: 1ο και τελευταίο στοιχείο της στήλης Pub_nbr σε κάθε TW
def pub_nbr_fun(data,tw_data):
    output_all=[]
    output1=data[data['Pub_nbr']>=tw_data[0][3]].reset_index(drop=True)
    output=output1[output1['Pub_nbr']<=tw_data[-1][3]].reset_index(drop=True)
    output_pub_nbr=list(output['Pub_nbr'])
    output_person_id=list(output['Person_id'])
    output_appln_id=list(output['Appln_id'])
    output_all=list(map(list,zip(output_pub_nbr,output_person_id,output_appln_id)))
    output_all.sort(key=takeZeroColumn)
    return output_all

# Συνάρτηση για να σκανάρω τις δύο λίστες (την αρχική λίστα με τα App/Inv
# που μίκρυνα πιο πάνω και τη λίστα με τις ημερομηνίες που έχουν Pub_nbr)
# και να κρατήσω μόνο τις σειρές με τα pub_nbrs που υπάρχουν και στις δύο λίστες
# Τα δεδομένα επιστρέφονται ταξινομημένα ως προς το DATE
def pub_nbr_person_id_fun(data,tw_data):
    output=[]
    k,l=0,0
    for i in range(k,len(tw_data)):
        for j in range(l,len(data)):
            if tw_data[i][3]==data[j][0]:
                output.append([data[j][0],data[j][1],data[j][2],tw_data[i][4]])
                l=j+1
            elif tw_data[i][3]<data[j][0]:
                break
            elif tw_data[i][3]>data[j][0]:
                pass
    output.sort(key=takeThirdColumn)
    return output

##### Συνάρτηση για εξαγωγή δεδομένων για κάθε κατηγορία πατέντας, βάσει του Appln_id. Επιστροφή αποτελεσμάτων ταξινομημένα ως προς το DATE
def appln_id_pub_nbr_person_id_fun(data,ipc_data):
    output=[]
    k,l=0,0
    for i in range(k,len(ipc_data)):
        for j in range(l,len(data)):
            if ipc_data[i][0]==data[j][2]:
                output.append([data[j][0],data[j][1],data[j][2],data[j][3]])
                l=j+1
            elif ipc_data[i][0]<data[j][2]:
                break
            elif ipc_data[i][0]>data[j][2]:
                pass
    output.sort(key=takeThirdColumn)
    return output


##### Συναρτήσεις για τη δημιουργία των δικτύων

# Συνάρτηση εντοπισμού των σμηνών μέσα στο δίκτυο
def component_dict_fun(data):
    clusters_dict=collections.defaultdict(list)
    clusters=[c for c in sorted(nx.connected_components(data), key=len, reverse=True)]
    for i,c in enumerate(clusters):
        for name in c:
            clusters_dict[i].append(name)
    nx.set_node_attributes(data, clusters_dict, 'components')
    return clusters_dict

# Συνάρτηση δημιουργίας των συνδέσεων του δικτύου
def creating_edges_fun_dynamical(data,step):
    links,clusters,size,net_edges,date=[],[],[],[],[]
    network=nx.Graph()
    k=0
    for i in range(len(data)-1):
        for j in range(i+1,len(data)):
            if data[i][0]==data[j][0] and data[i][1]!=data[j][1]:
                links.append([data[i][1],data[j][1]])
                k=k+1
                if k%step==0:
                    network.add_edges_from(links)
                    clusters=component_dict_fun(network)
                    size.append([len(clusters[0]),len(clusters[1]),len(clusters[2]),len(clusters[3]),len(clusters[4])])
                    net_edges.append(network.number_of_edges())
                    links.clear()
                    date.append(str(data[i][3][0:4])+'/'+str(data[i][3][4:6])+'/'+str(data[i][3][6:8]))
            else:
                break
    return net_edges, size, date


##### EPO_App_reg #####

# Αρχική λίστα με Pub_nbrs, Person_ids, Appln_id για μικρότερη αναζήτηση στη συνέχεια
EPO_App_reg_TW=[]
for i in range(len(All_time_windows)):
    EPO_App_reg_TW.append(pub_nbr_fun(EPO_App_reg,All_time_windows[i]))

# Τελική λίστα Pub_nbrs, Person_ids, Appln_id και Dates για κάθε TW μετά την αντιστοίχιση στις 2 λίστες.
EPO_App_reg_Pub_nbr_Person_id=[]
for i in range(len(All_time_windows)):
    EPO_App_reg_Pub_nbr_Person_id.append(pub_nbr_person_id_fun(EPO_App_reg_TW[i],All_time_windows[i]))


### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg=[]
links_EPO_App_reg,sizes_EPO_App_reg,dates_EPO_App_reg=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_App_reg=creating_edges_fun_dynamical(EPO_App_reg_Pub_nbr_Person_id[i],50)
    links_EPO_App_reg.append(mixed_edges_clusters_EPO_App_reg[0])
    sizes_EPO_App_reg.append(mixed_edges_clusters_EPO_App_reg[1])
    dates_EPO_App_reg.append(mixed_edges_clusters_EPO_App_reg[2])


### Γραφική Παρασταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_App_reg[k])):
            axes[i][j].plot(links_EPO_App_reg[k][l],sizes_EPO_App_reg[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_App_reg[k][l],sizes_EPO_App_reg[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_App_reg[k][l],sizes_EPO_App_reg[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_App_reg[k][l],sizes_EPO_App_reg[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_App_reg[k][l],sizes_EPO_App_reg[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_App_reg - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_TW_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_App_reg[i])):
        EPO_App_reg_TW_DataPlot[i].append([links_EPO_App_reg[i][j],\
                                           sizes_EPO_App_reg[i][j][0],\
                                           sizes_EPO_App_reg[i][j][1],\
                                           sizes_EPO_App_reg[i][j][2],\
                                           sizes_EPO_App_reg[i][j][3],\                                           
                                           sizes_EPO_App_reg[i][j][4]])

for key,value in EPO_App_reg_TW_DataPlot.items():
    with open('EPO_App_reg__TW_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_TW=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_App_reg[i])):
        EPO_App_reg_TW[i].append([dates_EPO_App_reg[i][j],sizes_EPO_App_reg[i][j]])

with open('EPO_App_reg__TW_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_TW.items():
        convert_file.write('%s:%s\n'%(key,value))


##### EPO_App_reg based on pantents' category #####

# Δημιουργία λίστας για καθε TW με Pub_nbr,Person_id,Appln_id,Dates ταξινομημένη ως προς το Appln_id
EPO_App_reg_Appln_id=[]
for i in range(len(All_time_windows)):
    EPO_App_reg_Appln_id.append(EPO_App_reg_Pub_nbr_Person_id[i])
    EPO_App_reg_Appln_id[i].sort(key=takeSecondColumn)


##### Patents "C": Chemistry; Metallurgy

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> C
EPO_App_reg_C_Pub_nbr_Person_id_Appl_id=[]
for i in tqdm(range(len(All_time_windows))):
    EPO_App_reg_C_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id[i],list_Ipc_C))

   
### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_C=[]
links_EPO_App_reg_C,sizes_EPO_App_reg_C,dates_EPO_App_reg_C=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_App_reg_C=creating_edges_fun_dynamical(EPO_App_reg_C_Pub_nbr_Person_id_Appl_id[i],50)
    links_EPO_App_reg_C.append(mixed_edges_clusters_EPO_App_reg_C[0])
    sizes_EPO_App_reg_C.append(mixed_edges_clusters_EPO_App_reg_C[1])
    dates_EPO_App_reg_C.append(mixed_edges_clusters_EPO_App_reg_C[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_App_reg_C[k])):
            axes[i][j].plot(links_EPO_App_reg_C[k][l],sizes_EPO_App_reg_C[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_C[k][l],sizes_EPO_App_reg_C[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_C[k][l],sizes_EPO_App_reg_C[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_C[k][l],sizes_EPO_App_reg_C[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_C[k][l],sizes_EPO_App_reg_C[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_App_reg - P.C. 'C' - T/W: "+str(k+1),size=18)
        k+=1


### Εξαγωγή δεδομένων
# Δεδομένα γραφικής παράστασης
EPO_App_reg_TW_C_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_App_reg_C[i])):
        EPO_App_reg_TW_C_DataPlot[i].append([links_EPO_App_reg_C[i][j],\
                                             sizes_EPO_App_reg_C[i][j][0],\
                                             sizes_EPO_App_reg_C[i][j][1],\
                                             sizes_EPO_App_reg_C[i][j][2],\
                                             sizes_EPO_App_reg_C[i][j][3],\
                                             sizes_EPO_App_reg_C[i][j][4]])

for key,value in EPO_App_reg_TW_C_DataPlot.items():
    with open('EPO_App_reg_TW_C_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_TW_C=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_App_reg_C[i])):
        EPO_App_reg_TW_C[i].append([dates_EPO_App_reg_C[i][j],sizes_EPO_App_reg_C[i][j]])

with open('EPO_App_reg_TW_C_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_TW_C.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "A": Human necessities

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> A
EPO_App_reg_A_Pub_nbr_Person_id_Appl_id=[]
for i in tqdm(range(len(All_time_windows))):
    EPO_App_reg_A_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id[i],list_Ipc_A))


### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_A=[]
links_EPO_App_reg_A,sizes_EPO_App_reg_A,dates_EPO_App_reg_A=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_App_reg_A=creating_edges_fun_dynamical(EPO_App_reg_A_Pub_nbr_Person_id_Appl_id[i],50)
    links_EPO_App_reg_A.append(mixed_edges_clusters_EPO_App_reg_A[0])
    sizes_EPO_App_reg_A.append(mixed_edges_clusters_EPO_App_reg_A[1])
    dates_EPO_App_reg_A.append(mixed_edges_clusters_EPO_App_reg_A[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_App_reg_A[k])):
            axes[i][j].plot(links_EPO_App_reg_A[k][l],sizes_EPO_App_reg_A[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_A[k][l],sizes_EPO_App_reg_A[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_A[k][l],sizes_EPO_App_reg_A[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_A[k][l],sizes_EPO_App_reg_A[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_A[k][l],sizes_EPO_App_reg_A[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_App_reg - P.C. 'A' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή δεδομένων
# Δεδομένα γραφικής παράστασης
EPO_App_reg_TW_A_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_App_reg_A[i])):
        EPO_App_reg_TW_A_DataPlot[i].append([links_EPO_App_reg_A[i][j],\
                                             sizes_EPO_App_reg_A[i][j][0],\
                                             sizes_EPO_App_reg_A[i][j][1],\
                                             sizes_EPO_App_reg_A[i][j][2],\
                                             sizes_EPO_App_reg_A[i][j][3],\
                                             sizes_EPO_App_reg_A[i][j][4]])

for key,value in EPO_App_reg_TW_A_DataPlot.items():
    with open('EPO_App_reg_TW_A_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_TW_A=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_App_reg_A[i])):
        EPO_App_reg_TW_A[i].append([dates_EPO_App_reg_A[i][j],sizes_EPO_App_reg_A[i][j]])

with open('EPO_App_reg_TW_A_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_TW_A.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "H": Electricity

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> H
EPO_App_reg_H_Pub_nbr_Person_id_Appl_id=[]
for i in tqdm(range(len(All_time_windows))):
    EPO_App_reg_H_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id[i],list_Ipc_H))


### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_H=[]
links_EPO_App_reg_H,sizes_EPO_App_reg_H,dates_EPO_App_reg_H=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_App_reg_H=creating_edges_fun_dynamical(EPO_App_reg_H_Pub_nbr_Person_id_Appl_id[i],50)
    links_EPO_App_reg_H.append(mixed_edges_clusters_EPO_App_reg_H[0])
    sizes_EPO_App_reg_H.append(mixed_edges_clusters_EPO_App_reg_H[1])
    dates_EPO_App_reg_H.append(mixed_edges_clusters_EPO_App_reg_H[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_App_reg_H[k])):
            axes[i][j].plot(links_EPO_App_reg_H[k][l],sizes_EPO_App_reg_H[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_H[k][l],sizes_EPO_App_reg_H[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_H[k][l],sizes_EPO_App_reg_H[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_H[k][l],sizes_EPO_App_reg_H[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_H[k][l],sizes_EPO_App_reg_H[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_App_reg - P.C. 'H' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_TW_H_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_App_reg_H[i])):
        EPO_App_reg_TW_H_DataPlot[i].append([links_EPO_App_reg_H[i][j],\
                                             sizes_EPO_App_reg_H[i][j][0],\
                                             sizes_EPO_App_reg_H[i][j][1],\
                                             sizes_EPO_App_reg_H[i][j][2],\
                                             sizes_EPO_App_reg_H[i][j][3],\
                                             sizes_EPO_App_reg_H[i][j][4]])

for key,value in EPO_App_reg_TW_H_DataPlot.items():
    with open('EPO_App_reg_TW_H_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_TW_H=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_App_reg_H[i])):
        EPO_App_reg_TW_H[i].append([dates_EPO_App_reg_H[i][j],sizes_EPO_App_reg_H[i][j]])

with open('EPO_App_reg_TW_H_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_TW_H.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "B": Performing Operations; Transporting

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> B
EPO_App_reg_B_Pub_nbr_Person_id_Appl_id=[]
for i in tqdm(range(len(All_time_windows))):
    EPO_App_reg_B_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id[i],list_Ipc_B))


### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_B=[]
links_EPO_App_reg_B,sizes_EPO_App_reg_B,dates_EPO_App_reg_B=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_App_reg_B=creating_edges_fun_dynamical(EPO_App_reg_B_Pub_nbr_Person_id_Appl_id[i],50)
    links_EPO_App_reg_B.append(mixed_edges_clusters_EPO_App_reg_B[0])
    sizes_EPO_App_reg_B.append(mixed_edges_clusters_EPO_App_reg_B[1])
    dates_EPO_App_reg_B.append(mixed_edges_clusters_EPO_App_reg_B[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_App_reg_B[k])):
            axes[i][j].plot(links_EPO_App_reg_B[k][l],sizes_EPO_App_reg_B[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_B[k][l],sizes_EPO_App_reg_B[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_B[k][l],sizes_EPO_App_reg_B[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_B[k][l],sizes_EPO_App_reg_B[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_B[k][l],sizes_EPO_App_reg_B[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_App_reg - P.C. 'B' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_TW_B_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_App_reg_B[i])):
        EPO_App_reg_TW_B_DataPlot[i].append([links_EPO_App_reg_B[i][j],\
                                             sizes_EPO_App_reg_B[i][j][0],\
                                             sizes_EPO_App_reg_B[i][j][1],\
                                             sizes_EPO_App_reg_B[i][j][2],\
                                             sizes_EPO_App_reg_B[i][j][3],\
                                             sizes_EPO_App_reg_B[i][j][4]])

for key,value in EPO_App_reg_TW_B_DataPlot.items():
    with open('EPO_App_reg_TW_B_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_TW_B=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_App_reg_B[i])):
        EPO_App_reg_TW_B[i].append([dates_EPO_App_reg_B[i][j],sizes_EPO_App_reg_B[i][j]])

with open('EPO_App_reg_TW_B_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_TW_B.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "G": Physics

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> G
EPO_App_reg_G_Pub_nbr_Person_id_Appl_id=[]
for i in tqdm(range(len(All_time_windows))):
    EPO_App_reg_G_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id[i],list_Ipc_G))


### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_G=[]
links_EPO_App_reg_G,sizes_EPO_App_reg_G,dates_EPO_App_reg_G=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_App_reg_G=creating_edges_fun_dynamical(EPO_App_reg_G_Pub_nbr_Person_id_Appl_id[i],50)
    links_EPO_App_reg_G.append(mixed_edges_clusters_EPO_App_reg_G[0])
    sizes_EPO_App_reg_G.append(mixed_edges_clusters_EPO_App_reg_G[1])
    dates_EPO_App_reg_G.append(mixed_edges_clusters_EPO_App_reg_G[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_App_reg_G[k])):
            axes[i][j].plot(links_EPO_App_reg_G[k][l],sizes_EPO_App_reg_G[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_G[k][l],sizes_EPO_App_reg_G[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_G[k][l],sizes_EPO_App_reg_G[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_G[k][l],sizes_EPO_App_reg_G[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_App_reg_G[k][l],sizes_EPO_App_reg_G[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_App_reg - P.C. 'G' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_TW_G_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_App_reg_G[i])):
        EPO_App_reg_TW_G_DataPlot[i].append([links_EPO_App_reg_G[i][j],\
                                             sizes_EPO_App_reg_G[i][j][0],\
                                             sizes_EPO_App_reg_G[i][j][1],\
                                             sizes_EPO_App_reg_G[i][j][2],\
                                             sizes_EPO_App_reg_G[i][j][3],\
                                             sizes_EPO_App_reg_G[i][j][4]])

for key,value in EPO_App_reg_TW_G_DataPlot.items():
    with open('EPO_App_reg_TW_G_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_TW_G=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_App_reg_Ipc_G[i])):
        EPO_App_reg_TW_G[i].append([dates_EPO_App_reg_G[i][j],sizes_EPO_App_reg_G[i][j]])

with open('EPO_App_reg_TW_G_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_TW_G.items():
        convert_file.write('%s:%s\n'%(key,value))


##### EPO_Inv_reg #####

# Αρχική λίστα με Pub_nbrs, Person_ids, Appln_id για μικρότερη αναζήτηση στη συνέχεια
EPO_Inv_reg_TW=[]
for i in range(len(All_time_windows)):
    EPO_Inv_reg_TW.append(pub_nbr_fun(EPO_Inv_reg,All_time_windows[i]))

# Τελική λίστα Pub_nbrs, Person_ids, Appln_id και Dates για κάθε TW μετά την αντιστοίχιση στις 2 λίστες.
EPO_Inv_reg_Pub_nbr_Person_id=[]
for i in range(len(All_time_windows)):
    EPO_Inv_reg_Pub_nbr_Person_id.append(pub_nbr_person_id_fun(EPO_Inv_reg_TW[i],All_time_windows[i]))
EPO_Inv_reg_Pub_nbr_Person_id


### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg=[]
links_EPO_Inv_reg,sizes_EPO_Inv_reg,dates_EPO_Inv_reg=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_Inv_reg=creating_edges_fun_dynamical(EPO_Inv_reg_Pub_nbr_Person_id[i],100)
    links_EPO_Inv_reg.append(mixed_edges_clusters_EPO_Inv_reg[0])
    sizes_EPO_Inv_reg.append(mixed_edges_clusters_EPO_Inv_reg[1])
    dates_EPO_Inv_reg.append(mixed_edges_clusters_EPO_Inv_reg[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_Inv_reg[k])):
            axes[i][j].plot(links_EPO_Inv_reg[k][l],sizes_EPO_Inv_reg[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg[k][l],sizes_EPO_Inv_reg[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg[k][l],sizes_EPO_Inv_reg[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg[k][l],sizes_EPO_Inv_reg[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg[k][l],sizes_EPO_Inv_reg[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_Inv_reg - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_TW_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_Inv_reg[i])):
        EPO_Inv_reg_TW_DataPlot[i].append([links_EPO_Inv_reg[i][j],\
                                           sizes_EPO_Inv_reg[i][j][0],\
                                           sizes_EPO_Inv_reg[i][j][1],\
                                           sizes_EPO_Inv_reg[i][j][2],\
                                           sizes_EPO_Inv_reg[i][j][3],\
                                           sizes_EPO_Inv_reg[i][j][4]])

for key,value in EPO_Inv_reg_TW_DataPlot.items():
    with open('EPO_Inv_reg__TW_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_TW=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_Inv_reg[i])):
        EPO_Inv_reg_TW[i].append([dates_EPO_Inv_reg[i][j],sizes_EPO_Inv_reg[i][j]])

with open('EPO_Inv_reg__TW_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_TW.items():
        convert_file.write('%s:%s\n'%(key,value))


##### EPO_Inv_reg based on pantents' category

# Δημιουργία λίστας για κάθε TW με Pub_nbr,Person_id,Appln_id,Dates ταξινομημένη ως προς το Appln_id
EPO_Inv_reg_Appln_id=[]
for i in range(len(All_time_windows)):
    EPO_Inv_reg_Appln_id.append(EPO_Inv_reg_Pub_nbr_Person_id[i])
    EPO_Inv_reg_Appln_id[i].sort(key=takeSecondColumn)


##### Patents "C": Chemistry; Metallurgy

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> C
EPO_Inv_reg_C_Pub_nbr_Person_id_Appl_id=[]
for i in range(len(All_time_windows)):
    EPO_Inv_reg_C_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id[i],list_Ipc_C))

# Ελάφρυνση μνήμης
del EPO_Inv_reg
del EP_Cit_Counts
del EPO_Ipc
EPO_Inv_reg_TW.clear()
EPO_Inv_reg_Pub_nbr_Person_id.clear()
test_list_EP_Cit_Counts.clear()
list_EP_Cit_Counts.clear()
All_Dates.clear()
list_Ipc_C.clear()

### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_C=[]
links_EPO_Inv_reg_C,sizes_EPO_Inv_reg_C,dates_EPO_Inv_reg_C=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_Inv_reg_C=creating_edges_fun_dynamical(EPO_Inv_reg_C_Pub_nbr_Person_id_Appl_id[i],100)
    links_EPO_Inv_reg_C.append(mixed_edges_clusters_EPO_Inv_reg_C[0])
    sizes_EPO_Inv_reg_C.append(mixed_edges_clusters_EPO_Inv_reg_C[1])
    dates_EPO_Inv_reg_C.append(mixed_edges_clusters_EPO_Inv_reg_C[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_Inv_reg_C[k])):
            axes[i][j].plot(links_EPO_Inv_reg_C[k][l],sizes_EPO_Inv_reg_C[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_C[k][l],sizes_EPO_Inv_reg_C[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_C[k][l],sizes_EPO_Inv_reg_C[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_C[k][l],sizes_EPO_Inv_reg_C[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_C[k][l],sizes_EPO_Inv_reg_C[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_Inv_reg - P.C. 'C' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_TW_C_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_Inv_reg_C[i])):
        EPO_Inv_reg_TW_C_DataPlot[i].append([links_EPO_Inv_reg_C[i][j],\
                                             sizes_EPO_Inv_reg_C[i][j][0],\
                                             sizes_EPO_Inv_reg_C[i][j][1],\
                                             sizes_EPO_Inv_reg_C[i][j][2],\ 
                                             sizes_EPO_Inv_reg_C[i][j][3],\
                                             sizes_EPO_Inv_reg_C[i][j][4]])

for key,value in EPO_Inv_reg_TW_C_DataPlot.items():
    with open('EPO_Inv_reg_TW_C_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_TW_C=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_Inv_reg_C[i])):
        EPO_Inv_reg_TW_C[i].append([dates_EPO_Inv_reg_C[i][j],sizes_EPO_Inv_reg_C[i][j]])

with open('EPO_Inv_reg_TW_C_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_TW_C.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "A": Human necessities

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> A
EPO_Inv_reg_A_Pub_nbr_Person_id_Appl_id=[]
for i in range(len(All_time_windows)):
    EPO_Inv_reg_A_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id[i],list_Ipc_A))

list_Ipc_A.clear() # Ελάφρυνση μνήμης

### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_A=[]
links_EPO_Inv_reg_A,sizes_EPO_Inv_reg_A,dates_EPO_Inv_reg_A=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_Inv_reg_A=creating_edges_fun_dynamical(EPO_Inv_reg_A_Pub_nbr_Person_id_Appl_id[i],100)
    links_EPO_Inv_reg_A.append(mixed_edges_clusters_EPO_Inv_reg_A[0])
    sizes_EPO_Inv_reg_A.append(mixed_edges_clusters_EPO_Inv_reg_A[1])
    dates_EPO_Inv_reg_A.append(mixed_edges_clusters_EPO_Inv_reg_A[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_Inv_reg_A[k])):
            axes[i][j].plot(links_EPO_Inv_reg_A[k][l],sizes_EPO_Inv_reg_A[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_A[k][l],sizes_EPO_Inv_reg_A[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_A[k][l],sizes_EPO_Inv_reg_A[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_A[k][l],sizes_EPO_Inv_reg_A[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_A[k][l],sizes_EPO_Inv_reg_A[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_Inv_reg - P.C. 'A' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_TW_A_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_Inv_reg_A[i])):
        EPO_Inv_reg_TW_A_DataPlot[i].append([links_EPO_Inv_reg_A[i][j],\
                                             sizes_EPO_Inv_reg_A[i][j][0],\
                                             sizes_EPO_Inv_reg_A[i][j][1],\
                                             sizes_EPO_Inv_reg_A[i][j][2],\
                                             sizes_EPO_Inv_reg_A[i][j][3],\
                                             sizes_EPO_Inv_reg_A[i][j][4]])

for key,value in EPO_Inv_reg_TW_A_DataPlot.items():
    with open('EPO_Inv_reg_TW_A_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_TW_A=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_Inv_reg_A[i])):
        EPO_Inv_reg_TW_A[i].append([dates_EPO_Inv_reg_A[i][j],sizes_EPO_Inv_reg_A[i][j]])

with open('EPO_Inv_reg_TW_A_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_TW_A.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "H": Electricity

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> H
EPO_Inv_reg_H_Pub_nbr_Person_id_Appl_id=[]
for i in range(len(All_time_windows)):
    EPO_Inv_reg_H_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id[i],list_Ipc_H))

list_Ipc_H.clear() # Ελάφρυνση μνήμης

### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_H=[]
links_EPO_Inv_reg_H,sizes_EPO_Inv_reg_H,dates_EPO_Inv_reg_H=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_Inv_reg_H=creating_edges_fun_dynamical(EPO_Inv_reg_H_Pub_nbr_Person_id_Appl_id[i],100)
    links_EPO_Inv_reg_H.append(mixed_edges_clusters_EPO_Inv_reg_H[0])
    sizes_EPO_Inv_reg_H.append(mixed_edges_clusters_EPO_Inv_reg_H[1])
    dates_EPO_Inv_reg_H.append(mixed_edges_clusters_EPO_Inv_reg_H[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_Inv_reg_H[k])):
            axes[i][j].plot(links_EPO_Inv_reg_H[k][l],sizes_EPO_Inv_reg_H[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_H[k][l],sizes_EPO_Inv_reg_H[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_H[k][l],sizes_EPO_Inv_reg_H[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_H[k][l],sizes_EPO_Inv_reg_H[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_H[k][l],sizes_EPO_Inv_reg_H[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_Inv_reg - P.C. 'H' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_TW_H_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_Inv_reg_H[i])):
        EPO_Inv_reg_TW_H_DataPlot[i].append([links_EPO_Inv_reg_H[i][j],\
                                             sizes_EPO_Inv_reg_H[i][j][0],\
                                             sizes_EPO_Inv_reg_H[i][j][1],\
                                             sizes_EPO_Inv_reg_H[i][j][2],\
                                             sizes_EPO_Inv_reg_H[i][j][3],\
                                             sizes_EPO_Inv_reg_H[i][j][4]])

for key,value in EPO_Inv_reg_TW_H_DataPlot.items():
    with open('EPO_Inv_reg_TW_H_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_TW_H=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_Inv_reg_H[i])):
        EPO_Inv_reg_TW_H[i].append([dates_EPO_Inv_reg_H[i][j],sizes_EPO_Inv_reg_H[i][j]])

with open('EPO_Inv_reg_TW_H_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_TW_H.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "B": Performing Operations; Transporting

#Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> B
EPO_Inv_reg_B_Pub_nbr_Person_id_Appl_id=[]
for i in range(len(All_time_windows)):
    EPO_Inv_reg_B_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id[i],list_Ipc_B))

list_Ipc_B.clear() # Ελάφρυνση μνήμης

### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_B=[]
links_EPO_Inv_reg_B,sizes_EPO_Inv_reg_B,dates_EPO_Inv_reg_B=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_Inv_reg_B=creating_edges_fun_dynamical(EPO_Inv_reg_B_Pub_nbr_Person_id_Appl_id[i],100)
    links_EPO_Inv_reg_B.append(mixed_edges_clusters_EPO_Inv_reg_B[0])
    sizes_EPO_Inv_reg_B.append(mixed_edges_clusters_EPO_Inv_reg_B[1])
    dates_EPO_Inv_reg_B.append(mixed_edges_clusters_EPO_Inv_reg_B[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_Inv_reg_B[k])):
            axes[i][j].plot(links_EPO_Inv_reg_B[k][l],sizes_EPO_Inv_reg_B[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_B[k][l],sizes_EPO_Inv_reg_B[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_B[k][l],sizes_EPO_Inv_reg_B[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_B[k][l],sizes_EPO_Inv_reg_B[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_B[k][l],sizes_EPO_Inv_reg_B[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_Inv_reg - P.C. 'B' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_TW_B_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_Inv_reg_B[i])):
        EPO_Inv_reg_TW_B_DataPlot[i].append([links_EPO_Inv_reg_B[i][j],\
                                             sizes_EPO_Inv_reg_B[i][j][0],\
                                             sizes_EPO_Inv_reg_B[i][j][1],\
                                             sizes_EPO_Inv_reg_B[i][j][2],\
                                             sizes_EPO_Inv_reg_B[i][j][3],\
                                             sizes_EPO_Inv_reg_B[i][j][4]])

for key,value in EPO_Inv_reg_TW_B_DataPlot.items():
    with open('EPO_Inv_reg_TW_B_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_TW_B=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_Inv_reg_B[i])):
        EPO_Inv_reg_TW_B[i].append([dates_EPO_Inv_reg_B[i][j],sizes_EPO_Inv_reg_B[i][j]])

with open('EPO_Inv_reg_TW_B_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_TW_B.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "G": Physics

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> G
EPO_Inv_reg_G_Pub_nbr_Person_id_Appl_id=[]
for i in range(len(All_time_windows)):
    EPO_Inv_reg_G_Pub_nbr_Person_id_Appl_id.append(appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id[i],list_Ipc_G))

list_Ipc_G.clear() # Ελάφρυνση μνήμης

### Δημιουργία συνδέσεων για κάθε TW και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_G=[]
links_EPO_Inv_reg_G,sizes_EPO_Inv_reg_G,dates_EPO_Inv_reg_G=[],[],[]
for i in tqdm(range(len(All_time_windows))):
    mixed_edges_clusters_EPO_Inv_reg_G=creating_edges_fun_dynamical(EPO_Inv_reg_G_Pub_nbr_Person_id_Appl_id[i],100)
    links_EPO_Inv_reg_G.append(mixed_edges_clusters_EPO_Inv_reg_G[0])
    sizes_EPO_Inv_reg_G.append(mixed_edges_clusters_EPO_Inv_reg_G[1])
    dates_EPO_Inv_reg_G.append(mixed_edges_clusters_EPO_Inv_reg_G[2])

### Γραφική Παράσταση
fig,axes=plt.subplots(nrows=int(len(All_time_windows)/3),ncols=int(len(All_time_windows)/12),figsize=(20,60),dpi=120)
fig.subplots_adjust(hspace=0.4)
fig.subplots_adjust(wspace=0.3)
k=0
for i in range (int(len(All_time_windows)/3)):
    for j in range (int(len(All_time_windows)/12)):
        for l in range(len(links_EPO_Inv_reg_G[k])):
            axes[i][j].plot(links_EPO_Inv_reg_G[k][l],sizes_EPO_Inv_reg_G[k][l][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_G[k][l],sizes_EPO_Inv_reg_G[k][l][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_G[k][l],sizes_EPO_Inv_reg_G[k][l][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_G[k][l],sizes_EPO_Inv_reg_G[k][l][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
            axes[i][j].plot(links_EPO_Inv_reg_G[k][l],sizes_EPO_Inv_reg_G[k][l][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
        axes[i][j].legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True,title="Legend",fancybox=True,prop={'size': 11})
        axes[i][j].locator_params(axis='both',nbins=5)
        axes[i][j].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.1f}'.format(x/1000)))
        axes[i][j].tick_params(axis='x', labelsize=15)
        axes[i][j].tick_params(axis='y', labelsize=15)
        axes[i][j].set_xlabel("Number of links (x$10^3$)",size=18)
        axes[i][j].set_ylabel("Cluster Size",size=18)
        axes[i][j].set_title("EPO_Inv_reg - P.C. 'G' - T/W: "+str(k+1),size=18)
        k+=1

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_TW_G_DataPlot=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(sizes_EPO_Inv_reg_G[i])):
        EPO_Inv_reg_TW_G_DataPlot[i].append([links_EPO_Inv_reg_G[i][j],\
                                             sizes_EPO_Inv_reg_G[i][j][0],\
                                             sizes_EPO_Inv_reg_G[i][j][1],\
                                             sizes_EPO_Inv_reg_G[i][j][2],\
                                             sizes_EPO_Inv_reg_G[i][j][3],\
                                             sizes_EPO_Inv_reg_G[i][j][4]])

for key,value in EPO_Inv_reg_TW_G_DataPlot.items():
    with open('EPO_Inv_reg_TW_G_DataPlot'+str(key)+'.txt', 'w') as convert_file:
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_TW_G=collections.defaultdict(list)
for i in range(len(All_time_windows)):
    for j in range(len(dates_EPO_Inv_reg_G[i])):
        EPO_Inv_reg_TW_G[i].append([dates_EPO_Inv_reg_G[i][j],sizes_EPO_Inv_reg_G[i][j]])

with open('EPO_Inv_reg_TW_G_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_TW_G.items():
        convert_file.write('%s:%s\n'%(key,value))
