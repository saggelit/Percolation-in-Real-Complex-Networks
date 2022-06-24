import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import collections
from tqdm.notebook import  tqdm
import matplotlib.ticker as ticker
import json


##### DATA #####

##### EP_Cit_Counts #####
EP_Cit_Counts=pd.read_table('201609_EP_Cit_Counts.txt',sep='|')

# Δημιουργία 2D λίστας με σπασμένες ημερομηνίες [YYYYMMDD] σε ξεχωριστές στήλες και EP_Pub_nbr
list_EP_Cit_Counts=list(map(list,zip(list(EP_Cit_Counts['EP_Pub_date']),list(EP_Cit_Counts['EP_Pub_nbr']))))
All_Dates=[]
for i in range(len(list_EP_Cit_Counts)):
    All_Dates.append([str(list_EP_Cit_Counts[i][0])[0:4],str(list_EP_Cit_Counts[i][0])[4:6],                      str(list_EP_Cit_Counts[i][0])[6:8],list_EP_Cit_Counts[i][1],str(list_EP_Cit_Counts[i][0])])

list_EP_Cit_Counts=All_Dates

# Αφαίρεση λανθασμένων καταχωρήσεων, διπλότυπων Pub_nbr και ταξινόμηση ως προς το Pub_nbr
indexes=[]
for i in range (len(list_EP_Cit_Counts)):
    if list_EP_Cit_Counts[i][0]=='9999' or len(list_EP_Cit_Counts[i][3])!=9:
        indexes.append(i)
indexes.sort(reverse=True)
for i in indexes:
    del list_EP_Cit_Counts[i]

test_list_EP_Cit_Counts=[list(t) for t in set(tuple(element) for element in list_EP_Cit_Counts)]
list_EP_Cit_Counts=sorted(test_list_EP_Cit_Counts,key=lambda l:l[3])


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



##### FUNCTIONS #####

##### Συναρτήσεις για εξαγωγή δεδομένων

# Συναρτήσεις για να παίρνει συγκεκριμένες στήλες από 2D list
def takeZeroColumn(elem):
    return elem[0]
def takeSecondColumn(elem):
    return elem[2]
def takeThirdColumn(elem):
    return elem[3]

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
    output.sort(key=takeThirdColumn) #sort by date gia na kanw tis syndeseis
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
    for i in tqdm(range(len(data)-1), desc='progress_out'):
        for j in range(i+1,len(data)):
            if data[i][0]==data[j][0] and data[i][1]!=data[j][1]:
                links.append((data[i][1],data[j][1]))
                k=k+1
                if k%step==0:
                    network.add_edges_from(links)
                    clusters=component_dict_fun(network)
                    size.append([len(clusters[0]),len(clusters[1]),len(clusters[2]),                                len(clusters[3]),len(clusters[4])])
                    net_edges.append(network.number_of_edges())
                    links.clear()
                    date.append(str(data[i][3][0:4])+'/'+str(data[i][3][4:6])+'/'+str(data[i][3][6:8]))
            else:
                break
    return net_edges, size, date


##### EPO_App_reg #####

# Δημιουργία λίστας από το αρχείο με Pub_nbr, Person_id,Appln_id ταξινομημένα ως προς Pub_nbr
EPO_App_reg_all=[]
EPO_App_reg_all=list(map(list,zip(EPO_App_reg['Pub_nbr'],EPO_App_reg['Person_id'],EPO_App_reg['Appln_id'])))

# Δημιουργία τελικής λίστας με Pub_nbr, Person_id, Appln_id, Dates, μόνο με τις τιμές που υπάρχουν και στα δύο αρχεία.
EPO_App_reg_Pub_nbr_Person_id=[]
EPO_App_reg_Pub_nbr_Person_id=pub_nbr_person_id_fun(EPO_App_reg_all,list_EP_Cit_Counts)


### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg=[]
links_EPO_App_reg,sizes_EPO_App_reg,dates_EPO_App_reg=[],[],[]
mixed_edges_clusters_EPO_App_reg=creating_edges_fun_dynamical(EPO_App_reg_Pub_nbr_Person_id,500)
links_EPO_App_reg=mixed_edges_clusters_EPO_App_reg[0]
sizes_EPO_App_reg=mixed_edges_clusters_EPO_App_reg[1]
dates_EPO_App_reg=mixed_edges_clusters_EPO_App_reg[2]

### Γραφική Παρασταση
for i in range (len(links_EPO_App_reg)):
    plt.plot(links_EPO_App_reg[i],sizes_EPO_App_reg[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_App_reg[i],sizes_EPO_App_reg[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_App_reg[i],sizes_EPO_App_reg[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_App_reg[i],sizes_EPO_App_reg[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_App_reg[i],sizes_EPO_App_reg[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'),shadow=True, title="Legend", fancybox=True,prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_App_reg - Full Network",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_App_reg)):
    EPO_App_reg_DataPlot[i].append([links_EPO_App_reg[i],sizes_EPO_App_reg[i][0],sizes_EPO_App_reg[i][1], sizes_EPO_App_reg[i][2],sizes_EPO_App_reg[i][3],sizes_EPO_App_reg[i][4]])

with open('FULL_EPO_App_reg__DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_App_reg_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_App_reg)):
    EPO_App_reg_Data[i].append([dates_EPO_App_reg[i],sizes_EPO_App_reg[i]])

with open('FULL_EPO_App_reg__Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### EPO_App_reg based on pantents' category #####

# Δημιουργία λίστας με Pub_nbr,Person_id,Appln_id,Dates ταξινομημένη ως προς το Appln_id
EPO_App_reg_Appln_id=[]
EPO_App_reg_Appln_id=EPO_App_reg_Pub_nbr_Person_id
EPO_App_reg_Appln_id.sort(key=takeSecondColumn)


##### Patents "C": Chemistry; Metallurgy

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> C
EPO_App_reg_C_Pub_nbr_Person_id_Appl_id=[]
EPO_App_reg_C_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id,list_Ipc_C)

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_C=[]
links_EPO_App_reg_C,sizes_EPO_App_reg_C,dates_EPO_App_reg_C=[],[],[]
mixed_edges_clusters_EPO_App_reg_C=creating_edges_fun_dynamical(EPO_App_reg_C_Pub_nbr_Person_id_Appl_id,500)
links_EPO_App_reg_C=mixed_edges_clusters_EPO_App_reg_C[0]
sizes_EPO_App_reg_C=mixed_edges_clusters_EPO_App_reg_C[1]
dates_EPO_App_reg_C=mixed_edges_clusters_EPO_App_reg_C[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_App_reg_C)):
    plt.plot(links_EPO_App_reg_C[i],sizes_EPO_App_reg_C[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_App_reg_C[i],sizes_EPO_App_reg_C[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_App_reg_C[i],sizes_EPO_App_reg_C[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_App_reg_C[i],sizes_EPO_App_reg_C[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_App_reg_C[i],sizes_EPO_App_reg_C[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True, prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_App_reg - Full Network - P.C. 'C'",size=18)
plt.show()

### Εξαγωγή δεδομένων
# Δεδομένα γραφικής παράστασης
EPO_App_reg_C_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_App_reg_C)):
    EPO_App_reg_C_DataPlot[i].append([links_EPO_App_reg_C[i],sizes_EPO_App_reg_C[i][0],sizes_EPO_App_reg_C[i][1], sizes_EPO_App_reg_C[i][2],sizes_EPO_App_reg_C[i][3],sizes_EPO_App_reg_C[i][4]])

with open('FULL_EPO_App_reg_C_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_App_reg_C_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_C_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_App_reg_C)):
    EPO_App_reg_C_Data[i].append([dates_EPO_App_reg_C[i],sizes_EPO_App_reg_C[i]])

with open('FULL_EPO_App_reg_C_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_C_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "A": Human necessities

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> A
EPO_App_reg_A_Pub_nbr_Person_id_Appl_id=[]
EPO_App_reg_A_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id,list_Ipc_A)

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_A=[]
links_EPO_App_reg_A,sizes_EPO_App_reg_A,dates_EPO_App_reg_A=[],[],[]
mixed_edges_clusters_EPO_App_reg_A=creating_edges_fun_dynamical(EPO_App_reg_A_Pub_nbr_Person_id_Appl_id,500)
links_EPO_App_reg_A=mixed_edges_clusters_EPO_App_reg_A[0]
sizes_EPO_App_reg_A=mixed_edges_clusters_EPO_App_reg_A[1]
dates_EPO_App_reg_A=mixed_edges_clusters_EPO_App_reg_A[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_App_reg_A)):
    plt.plot(links_EPO_App_reg_A[i],sizes_EPO_App_reg_A[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_App_reg_A[i],sizes_EPO_App_reg_A[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_App_reg_A[i],sizes_EPO_App_reg_A[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_App_reg_A[i],sizes_EPO_App_reg_A[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_App_reg_A[i],sizes_EPO_App_reg_A[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True,prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_App_reg - Full Network - P.C. 'A'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_A_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_App_reg_A)):
    EPO_App_reg_A_DataPlot[i].append([links_EPO_App_reg_A[i], sizes_EPO_App_reg_A[i][0], sizes_EPO_App_reg_A[i][1], sizes_EPO_App_reg_A[i][2],   sizes_EPO_App_reg_A[i][3], sizes_EPO_App_reg_A[i][4]])

with open('FULL_EPO_App_reg_A_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_App_reg_A_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_A_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_App_reg_A)):
    EPO_App_reg_A_Data[i].append([dates_EPO_App_reg_A[i],sizes_EPO_App_reg_A[i]])

with open('FULL_EPO_App_reg_A_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_A_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "H": Electricity

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> H
EPO_App_reg_H_Pub_nbr_Person_id_Appl_id=[]
EPO_App_reg_H_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id,list_Ipc_H)

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_H=[]
links_EPO_App_reg_H,sizes_EPO_App_reg_H,dates_EPO_App_reg_H=[],[],[]
mixed_edges_clusters_EPO_App_reg_H=creating_edges_fun_dynamical(EPO_App_reg_H_Pub_nbr_Person_id_Appl_id,500)
links_EPO_App_reg_H=mixed_edges_clusters_EPO_App_reg_H[0]
sizes_EPO_App_reg_H=mixed_edges_clusters_EPO_App_reg_H[1]
dates_EPO_App_reg_H=mixed_edges_clusters_EPO_App_reg_H[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_App_reg_H)):
    plt.plot(links_EPO_App_reg_H[i],sizes_EPO_App_reg_H[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_App_reg_H[i],sizes_EPO_App_reg_H[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_App_reg_H[i],sizes_EPO_App_reg_H[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_App_reg_H[i],sizes_EPO_App_reg_H[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_App_reg_H[i],sizes_EPO_App_reg_H[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True,prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_App_reg - Full Network - P.C. 'H'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_H_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_App_reg_H)):
    EPO_App_reg_H_DataPlot[i].append([links_EPO_App_reg_H[i], sizes_EPO_App_reg_H[i][0], sizes_EPO_App_reg_H[i][1], sizes_EPO_App_reg_H[i][2], sizes_EPO_App_reg_H[i][3], sizes_EPO_App_reg_H[i][4]])

with open('FULL_EPO_App_reg_H_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_App_reg_H_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_H_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_App_reg_H)):
    EPO_App_reg_H_Data[i].append([dates_EPO_App_reg_H[i],sizes_EPO_App_reg_H[i]])

with open('FULL_EPO_App_reg_H_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_H_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "B": Performing Operations; Transporting

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> B
EPO_App_reg_B_Pub_nbr_Person_id_Appl_id=[]
EPO_App_reg_B_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id,list_Ipc_B)


### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_B=[]
links_EPO_App_reg_B,sizes_EPO_App_reg_B,dates_EPO_App_reg_B=[],[],[]
mixed_edges_clusters_EPO_App_reg_B=creating_edges_fun_dynamical(EPO_App_reg_B_Pub_nbr_Person_id_Appl_id,500)
links_EPO_App_reg_B=mixed_edges_clusters_EPO_App_reg_B[0]
sizes_EPO_App_reg_B=mixed_edges_clusters_EPO_App_reg_B[1]
dates_EPO_App_reg_B=mixed_edges_clusters_EPO_App_reg_B[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_App_reg_B)):
    plt.plot(links_EPO_App_reg_B[i],sizes_EPO_App_reg_B[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_App_reg_B[i],sizes_EPO_App_reg_B[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_App_reg_B[i],sizes_EPO_App_reg_B[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_App_reg_B[i],sizes_EPO_App_reg_B[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_App_reg_B[i],sizes_EPO_App_reg_B[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True,prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_App_reg - Full Network - P.C. 'B'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_B_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_App_reg_B)):
    EPO_App_reg_B_DataPlot[i].append([links_EPO_App_reg_B[i], sizes_EPO_App_reg_B[i][0], sizes_EPO_App_reg_B[i][1], sizes_EPO_App_reg_B[i][2], sizes_EPO_App_reg_B[i][3], sizes_EPO_App_reg_B[i][4]])

with open('FULL_EPO_App_reg_B_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_App_reg_B_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_B_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_App_reg_B)):
    EPO_App_reg_B_Data[i].append([dates_EPO_App_reg_B[i],sizes_EPO_App_reg_B[i]])

with open('FULL_EPO_App_reg_B_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_B_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "G": Physics

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> G
EPO_App_reg_G_Pub_nbr_Person_id_Appl_id=[]
EPO_App_reg_G_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_App_reg_Appln_id,list_Ipc_G)


### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_App_reg_G=[]
links_EPO_App_reg_G,sizes_EPO_App_reg_G,dates_EPO_App_reg_G=[],[],[]
mixed_edges_clusters_EPO_App_reg_G=creating_edges_fun_dynamical(EPO_App_reg_G_Pub_nbr_Person_id_Appl_id,500)
links_EPO_App_reg_G=mixed_edges_clusters_EPO_App_reg_G[0]
sizes_EPO_App_reg_G=mixed_edges_clusters_EPO_App_reg_G[1]
dates_EPO_App_reg_G=mixed_edges_clusters_EPO_App_reg_G[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_App_reg_G)):
    plt.plot(links_EPO_App_reg_G[i],sizes_EPO_App_reg_G[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_App_reg_G[i],sizes_EPO_App_reg_G[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_App_reg_G[i],sizes_EPO_App_reg_G[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_App_reg_G[i],sizes_EPO_App_reg_G[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_App_reg_G[i],sizes_EPO_App_reg_G[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True,prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_App_reg - Full Network - P.C. 'G'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_App_reg_G_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_App_reg_G)):
    EPO_App_reg_G_DataPlot[i].append([links_EPO_App_reg_G[i], sizes_EPO_App_reg_G[i][0], sizes_EPO_App_reg_G[i][1], sizes_EPO_App_reg_G[i][2], sizes_EPO_App_reg_G[i][3], sizes_EPO_App_reg_G[i][4]])

with open('FULL_EPO_App_reg_G_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_App_reg_G_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_App_reg_G_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_App_reg_G)):
    EPO_App_reg_G_Data[i].append([dates_EPO_App_reg_G[i],sizes_EPO_App_reg_G[i]])

with open('FULL_EPO_App_reg_G_Data.txt', 'w') as convert_file:
     for key,value in EPO_App_reg_G_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### EPO_Inv_reg #####

# Δημιουργία λίστας από το αρχείο με Pub_nbr, Person_id,Appln_id ταξινομημένα ως προς Pub_nbr
EPO_Inv_reg_all=[]
EPO_Inv_reg_all=list(map(list,zip(EPO_Inv_reg['Pub_nbr'],EPO_Inv_reg['Person_id'],EPO_Inv_reg['Appln_id'])))

# Τελική λίστα με Pub_nbr, Person_id, Appln_id, Dates, μόνο με τις τιμές που υπάρχουν και στα δύο αρχεία.
EPO_Inv_reg_Pub_nbr_Person_id=[]
EPO_Inv_reg_Pub_nbr_Person_id=pub_nbr_person_id_fun(EPO_Inv_reg_all,list_EP_Cit_Counts)

# Ελάφρυνση μνήμης
del EP_Cit_Counts
list_EP_Cit_Counts.clear()
test_list_EP_Cit_Counts.clear()
All_Dates.clear()
del EPO_Inv_reg
EPO_Inv_reg_all.clear()

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg=[]
links_EPO_Inv_reg,sizes_EPO_Inv_reg,dates_EPO_Inv_reg=[],[],[]
mixed_edges_clusters_EPO_Inv_reg=creating_edges_fun_dynamical(EPO_Inv_reg_Pub_nbr_Person_id,1000)
links_EPO_Inv_reg=mixed_edges_clusters_EPO_Inv_reg[0]
sizes_EPO_Inv_reg=mixed_edges_clusters_EPO_Inv_reg[1]
dates_EPO_Inv_reg=mixed_edges_clusters_EPO_Inv_reg[2]

### Γραφική Παράσταση
for i in range (len(links_EPO_Inv_reg)):
    plt.plot(links_EPO_Inv_reg[i],sizes_EPO_Inv_reg[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_Inv_reg[i],sizes_EPO_Inv_reg[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_Inv_reg[i],sizes_EPO_Inv_reg[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_Inv_reg[i],sizes_EPO_Inv_reg[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_Inv_reg[i],sizes_EPO_Inv_reg[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True, prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_Inv_reg - Full Network",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_Inv_reg)):
    EPO_Inv_reg_DataPlot[i].append([links_EPO_Inv_reg[i], sizes_EPO_Inv_reg[i][0], sizes_EPO_Inv_reg[i][1], sizes_EPO_Inv_reg[i][2], sizes_EPO_Inv_reg[i][3], sizes_EPO_Inv_reg[i][4]])

with open('FULL_EPO_Inv_reg__DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_Inv_reg_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_Inv_reg)):
    EPO_Inv_reg_Data[i].append([dates_EPO_Inv_reg[i],sizes_EPO_Inv_reg[i]])

with open('FULL_EPO_Inv_reg__Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### EPO_Inv_reg based on pantents' category

# Δημιουργία λίστας με Pub_nbr,Person_id,Appln_id,Dates ταξινομημένη ως προς το Appln_id
EPO_Inv_reg_Appln_id=[]
EPO_Inv_reg_Appln_id=EPO_Inv_reg_Pub_nbr_Person_id
EPO_Inv_reg_Appln_id.sort(key=takeSecondColumn)


##### Patents "C": Chemistry; Metallurgy

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> C
EPO_Inv_reg_C_Pub_nbr_Person_id_Appl_id=[]
EPO_Inv_reg_C_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id,list_Ipc_C)

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_C=[]
links_EPO_Inv_reg_C,sizes_EPO_Inv_reg_C,dates_EPO_Inv_reg_C=[],[],[]
mixed_edges_clusters_EPO_Inv_reg_C=creating_edges_fun_dynamical(EPO_Inv_reg_C_Pub_nbr_Person_id_Appl_id,1000)
links_EPO_Inv_reg_C=mixed_edges_clusters_EPO_Inv_reg_C[0]
sizes_EPO_Inv_reg_C=mixed_edges_clusters_EPO_Inv_reg_C[1]
dates_EPO_Inv_reg_C=mixed_edges_clusters_EPO_Inv_reg_C[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_Inv_reg_C)):
    plt.plot(links_EPO_Inv_reg_C[i],sizes_EPO_Inv_reg_C[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_Inv_reg_C[i],sizes_EPO_Inv_reg_C[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_Inv_reg_C[i],sizes_EPO_Inv_reg_C[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_Inv_reg_C[i],sizes_EPO_Inv_reg_C[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_Inv_reg_C[i],sizes_EPO_Inv_reg_C[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True, prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_Inv_reg - Full Network - P.C. 'C'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_C_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_Inv_reg_C)):
    EPO_Inv_reg_C_DataPlot[i].append([links_EPO_Inv_reg_C[i], sizes_EPO_Inv_reg_C[i][0], sizes_EPO_Inv_reg_C[i][1], sizes_EPO_Inv_reg_C[i][2], sizes_EPO_Inv_reg_C[i][3], sizes_EPO_Inv_reg_C[i][4]])

with open('FULL_EPO_Inv_reg_C_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_Inv_reg_C_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_C_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_Inv_reg_C)):
    EPO_Inv_reg_C_Data[i].append([dates_EPO_Inv_reg_C[i],sizes_EPO_Inv_reg_C[i]])

with open('FULL_EPO_Inv_reg_C_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_C_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "A": Human necessities

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> A
EPO_Inv_reg_A_Pub_nbr_Person_id_Appl_id=[]
EPO_Inv_reg_A_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id,list_Ipc_A)

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_A=[]
links_EPO_Inv_reg_A,sizes_EPO_Inv_reg_A,dates_EPO_Inv_reg_A=[],[],[]
mixed_edges_clusters_EPO_Inv_reg_A=creating_edges_fun_dynamical(EPO_Inv_reg_A_Pub_nbr_Person_id_Appl_id,1000)
links_EPO_Inv_reg_A=mixed_edges_clusters_EPO_Inv_reg_A[0]
sizes_EPO_Inv_reg_A=mixed_edges_clusters_EPO_Inv_reg_A[1]
dates_EPO_Inv_reg_A=mixed_edges_clusters_EPO_Inv_reg_A[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_Inv_reg_A)):
    plt.plot(links_EPO_Inv_reg_A[i],sizes_EPO_Inv_reg_A[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_Inv_reg_A[i],sizes_EPO_Inv_reg_A[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_Inv_reg_A[i],sizes_EPO_Inv_reg_A[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_Inv_reg_A[i],sizes_EPO_Inv_reg_A[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_Inv_reg_A[i],sizes_EPO_Inv_reg_A[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True, prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_Inv_reg - Full Network - P.C. 'A'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_A_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_Inv_reg_A)):
    EPO_Inv_reg_A_DataPlot[i].append([links_EPO_Inv_reg_A[i], sizes_EPO_Inv_reg_A[i][0], sizes_EPO_Inv_reg_A[i][1], sizes_EPO_Inv_reg_A[i][2], sizes_EPO_Inv_reg_A[i][3], sizes_EPO_Inv_reg_A[i][4]])

with open('FULL_EPO_Inv_reg_A_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_Inv_reg_A_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_A_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_Inv_reg_A)):
    EPO_Inv_reg_A_Data[i].append([dates_EPO_Inv_reg_A[i],sizes_EPO_Inv_reg_A[i]])

with open('FULL_EPO_Inv_reg_A_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_A_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "H": Electricity

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> H
EPO_Inv_reg_H_Pub_nbr_Person_id_Appl_id=[]
EPO_Inv_reg_H_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id,list_Ipc_H)

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_H=[]
links_EPO_Inv_reg_H,sizes_EPO_Inv_reg_H,dates_EPO_Inv_reg_H=[],[],[]
mixed_edges_clusters_EPO_Inv_reg_H=creating_edges_fun_dynamical(EPO_Inv_reg_H_Pub_nbr_Person_id_Appl_id,1000)
links_EPO_Inv_reg_H=mixed_edges_clusters_EPO_Inv_reg_H[0]
sizes_EPO_Inv_reg_H=mixed_edges_clusters_EPO_Inv_reg_H[1]
dates_EPO_Inv_reg_H=mixed_edges_clusters_EPO_Inv_reg_H[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_Inv_reg_H)):
    plt.plot(links_EPO_Inv_reg_H[i],sizes_EPO_Inv_reg_H[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_Inv_reg_H[i],sizes_EPO_Inv_reg_H[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_Inv_reg_H[i],sizes_EPO_Inv_reg_H[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_Inv_reg_H[i],sizes_EPO_Inv_reg_H[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_Inv_reg_H[i],sizes_EPO_Inv_reg_H[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True, prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_Inv_reg - Full Network - P.C. 'H'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_H_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_Inv_reg_H)):
    EPO_Inv_reg_H_DataPlot[i].append([links_EPO_Inv_reg_H[i], sizes_EPO_Inv_reg_H[i][0], sizes_EPO_Inv_reg_H[i][1], sizes_EPO_Inv_reg_H[i][2], sizes_EPO_Inv_reg_H[i][3], sizes_EPO_Inv_reg_H[i][4]])

with open('FULL_EPO_Inv_reg_H_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_Inv_reg_H_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_H_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_Inv_reg_H)):
    EPO_Inv_reg_H_Data[i].append([dates_EPO_Inv_reg_H[i],sizes_EPO_Inv_reg_H[i]])

with open('FULL_EPO_Inv_reg_H_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_H_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "B": Performing Operations; Transporting

# Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> B
EPO_Inv_reg_B_Pub_nbr_Person_id_Appl_id=[]
EPO_Inv_reg_B_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id,list_Ipc_B)

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_B=[]
links_EPO_Inv_reg_B,sizes_EPO_Inv_reg_B,dates_EPO_Inv_reg_B=[],[],[]
mixed_edges_clusters_EPO_Inv_reg_B=creating_edges_fun_dynamical(EPO_Inv_reg_B_Pub_nbr_Person_id_Appl_id,1000)
links_EPO_Inv_reg_B=mixed_edges_clusters_EPO_Inv_reg_B[0]
sizes_EPO_Inv_reg_B=mixed_edges_clusters_EPO_Inv_reg_B[1]
dates_EPO_Inv_reg_B=mixed_edges_clusters_EPO_Inv_reg_B[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_Inv_reg_B)):
    plt.plot(links_EPO_Inv_reg_B[i],sizes_EPO_Inv_reg_B[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_Inv_reg_B[i],sizes_EPO_Inv_reg_B[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_Inv_reg_B[i],sizes_EPO_Inv_reg_B[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_Inv_reg_B[i],sizes_EPO_Inv_reg_B[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_Inv_reg_B[i],sizes_EPO_Inv_reg_B[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True, prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_Inv_reg - Full Network - P.C. 'B'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_B_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_Inv_reg_B)):
    EPO_Inv_reg_B_DataPlot[i].append([links_EPO_Inv_reg_B[i], sizes_EPO_Inv_reg_B[i][0], sizes_EPO_Inv_reg_B[i][1], sizes_EPO_Inv_reg_B[i][2], sizes_EPO_Inv_reg_B[i][3],sizes_EPO_Inv_reg_B[i][4]])

with open('FULL_EPO_Inv_reg_B_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_Inv_reg_B_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_B_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_Inv_reg_B)):
    EPO_Inv_reg_B_Data[i].append([dates_EPO_Inv_reg_B[i],sizes_EPO_Inv_reg_B[i]])

with open('FULL_EPO_Inv_reg_B_Data.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_B_Data.items():
        convert_file.write('%s:%s\n'%(key,value))


##### Patents "G": Physics

#  Aντιστοίχιση για να κρατήσω μόνο τις σειρές με appln_id -> G
EPO_Inv_reg_G_Pub_nbr_Person_id_Appl_id=[]
EPO_Inv_reg_G_Pub_nbr_Person_id_Appl_id=appln_id_pub_nbr_person_id_fun(EPO_Inv_reg_Appln_id,list_Ipc_G)

### Δημιουργία των συνδέσεων και εξαγωγή σε λίστες των τελικών συνδέσεων,
### του μεγέθους των σμηνών στο δίκτυο και τις αντίστοιχες ημερομηνίες
mixed_edges_clusters_EPO_Inv_reg_G=[]
links_EPO_Inv_reg_G,sizes_EPO_Inv_reg_G,dates_EPO_Inv_reg_G=[],[],[]
mixed_edges_clusters_EPO_Inv_reg_G=creating_edges_fun_dynamical(EPO_Inv_reg_G_Pub_nbr_Person_id_Appl_id,1000)
links_EPO_Inv_reg_G=mixed_edges_clusters_EPO_Inv_reg_G[0]
sizes_EPO_Inv_reg_G=mixed_edges_clusters_EPO_Inv_reg_G[1]
dates_EPO_Inv_reg_G=mixed_edges_clusters_EPO_Inv_reg_G[2]

### Γραφική Παράσταση
for i in range(len(links_EPO_Inv_reg_G)):
    plt.plot(links_EPO_Inv_reg_G[i],sizes_EPO_Inv_reg_G[i][0],'^',ms=4,markeredgewidth=0.5,mec='r',mfc='none')
    plt.plot(links_EPO_Inv_reg_G[i],sizes_EPO_Inv_reg_G[i][1],'*',ms=4,markeredgewidth=0.5,mec='g',mfc='none')
    plt.plot(links_EPO_Inv_reg_G[i],sizes_EPO_Inv_reg_G[i][2],'<',ms=4,markeredgewidth=0.5,mec='b',mfc='none')
    plt.plot(links_EPO_Inv_reg_G[i],sizes_EPO_Inv_reg_G[i][3],'>',ms=4,markeredgewidth=0.5,mec='c',mfc='none')
    plt.plot(links_EPO_Inv_reg_G[i],sizes_EPO_Inv_reg_G[i][4],'s',ms=4,markeredgewidth=0.5,mec='y',mfc='none')
plt.legend(('1st cluster','2nd cluster','3rd cluster','4th cluster','5th cluster'), shadow=True, title="Legend", fancybox=True, prop={'size': 11})
plt.locator_params(axis='both',nbins=5)
x_values = plt.gca().get_xticks()
plt.gca().set_xticklabels(['{:,.1f}'.format(x/1000) for x in x_values])
y_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.1f}'.format(y/1000) for y in y_values])
plt.xticks(size=15)
plt.yticks(size=15)
plt.xlabel("Number of links (x$10^3$)",size=18)
plt.ylabel("Cluster Size (x$10^3$)",size=18)
plt.title("EPO_Inv_reg - Full Network - P.C. 'G'",size=18)
plt.show()

### Εξαγωγή Δεδομένων σε αρχεία
# Δεδομένα γραφικής παράστασης
EPO_Inv_reg_G_DataPlot=collections.defaultdict(list)
for i in range(len(sizes_EPO_Inv_reg_G)):
    EPO_Inv_reg_G_DataPlot[i].append([links_EPO_Inv_reg_G[i], sizes_EPO_Inv_reg_G[i][0], sizes_EPO_Inv_reg_G[i][1], sizes_EPO_Inv_reg_G[i][2], sizes_EPO_Inv_reg_G[i][3], sizes_EPO_Inv_reg_G[i][4]])

with open('FULL_EPO_Inv_reg_G_DataPlot.txt', 'w') as convert_file:
    for key,value in EPO_Inv_reg_G_DataPlot.items():
        for x,y,z,w,q,t in value:
            convert_file.write('%s|%s|%s|%s|%s|%s\n'%(x,y,z,w,q,t))

# Δεδομένα ημερομηνιών και μεγέθους των σμηνών
EPO_Inv_reg_G_Data=collections.defaultdict(list)
for i in range(len(dates_EPO_Inv_reg_G)):
    EPO_Inv_reg_G_Data[i].append([dates_EPO_Inv_reg_G[i],sizes_EPO_Inv_reg_G[i]])

with open('FULL_EPO_Inv_reg_G.txt', 'w') as convert_file:
     for key,value in EPO_Inv_reg_G_Data.items():
        convert_file.write('%s:%s\n'%(key,value))
