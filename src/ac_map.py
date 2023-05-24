import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
from fuzzywuzzy import process
import json


#defining directories
dir_path=Path(__file__).resolve().parents[1]
raw_data_path= dir_path.joinpath("data/raw")
interim_data_path= dir_path.joinpath("data/interim/ac_mapped")
external_data_path= dir_path.joinpath("data/external")

pc_mapper_json=interim_data_path.joinpath("pc_mapper.json")
ac_mapper_json=interim_data_path.joinpath("ac_mapper.json")

final_file=interim_data_path.joinpath("ac_map.shp")

if not interim_data_path.exists():
    interim_data_path.mkdir(parents=True)


#reading in the shape file
ac_shp_files=list(external_data_path.joinpath('ac_shp').glob("*.shp"))
ac_shp=gpd.read_file(str(ac_shp_files[0]))

# cleaning shape file

col_names=ac_shp.columns
col_names=[x.lower() for x in col_names]
ac_shp.columns=col_names

for col in ['st_name','pc_name','ac_name']:

    ac_shp[col]=ac_shp[col].str.lower().str.strip().str.replace(" ", "_")

#adding data for Telangana, Ladakh
telangana_pcs=['adilabad(st)', 
               'peddapalle_(sc)', 
               'karimnagar', 
               'nizamabad', 
               'zahirabad', 
               'medak', 
               'malkajgiri', 
               'secunderabad', 
               'hyderabad', 
               'chevella', 
               'mahbubnagar', 
               'nagarkurnool(sc)', 
               'nalgonda',
               'bhongir', 
               'warangal(sc)', 
               'mahabubabad(st)', 
               'khammam',
            ]
ac_shp['st_name']=np.where(ac_shp['pc_name'].isin(telangana_pcs), "telangana", ac_shp['st_name'])
ac_shp['st_name']=np.where(ac_shp['pc_name']=='ladakh', "ladakh", ac_shp['st_name'])


#creating an new string value in shp file by concatentaing state, pc, ac
ac_shp['pc_id']=ac_shp['st_name']+"_"+ac_shp['pc_name']
ac_shp['ac_id']=ac_shp['st_name']+"_"+ac_shp['pc_name']+"_"+ac_shp['ac_name']

ac_shp_pc_list=ac_shp['pc_id'].unique()
ac_shp_ac_list=ac_shp['ac_id'].unique()



#reading in the master file
master_path=list(raw_data_path.glob("*.xlsx"))
df=pd.read_excel(master_path[0], sheet_name='master_list')

# cleaning master file
col_names=df.columns
col_names=[x.lower().strip() for x in col_names]
df.columns=col_names

#creating an new string value in shp file by concatentaing state, pc, ac

for col in ['state', 'parliamentary constituency','assembly constituency']:
    df[col]=df[col].str.lower().str.strip().str.replace(" ", "_")

    
df['pc_id']=df['state']+"_"+df['parliamentary constituency']
df['ac_id']=df['state']+"_"+df['parliamentary constituency']+"_"+df['assembly constituency']

df_pc_list=df['pc_id'].unique()
df_ac_list=df['ac_id'].unique()


# fuzzy matching PC
pc_match=[process.extractOne(i, ac_shp_pc_list)
        for i in df_pc_list]

pc_match = pd.DataFrame(pc_match, columns=["match", "score"])

mapper_df_pc = pd.concat(
    [pd.Series(df_pc_list), pc_match],
    axis=1,
    ignore_index=True,
    names=["original", "match", "score"],
)

print(mapper_df_pc[mapper_df_pc[2] < 80]) # this threshhold has been manually verified. Anything less than 70% is wrong.


# # mapper_df_pc = mapper_df_pc[mapper_df_pc[2] >= 90]


# creating a PC dictionary
pc_dict = dict(zip(mapper_df_pc[0], mapper_df_pc[1]))

with open(str(pc_mapper_json), "w") as out_file:
    json.dump(pc_dict, out_file)




# fuzzy matching AC
# ac_match=[process.extractOne(i, ac_shp_ac_list)
#         for i in df_ac_list]

# ac_match = pd.DataFrame(ac_match, columns=["match", "score"])

# mapper_df_ac = pd.concat(
#     [pd.Series(df_ac_list), ac_match],
#     axis=1,
#     ignore_index=True,
#     names=["original", "match", "score"],
# )

# # # mapper_df = mapper_df[mapper_df[2] >= 90]


# # creating a dictionary for fuzzy mapper
# ac_dict = dict(zip(mapper_df_ac[0], mapper_df_ac[1]))

# print(ac_dict)





# # applying the mapper dictionary on the original processed state file to correct for fuzzy matched names
# master_df["parliamentary constituency "] = master_df["parliamentary constituency "].replace(mapper_dict)
# master_df['dups']=master_df.duplicated(['state', 'parliamentary constituency '], keep=False)
# print(master_df[master_df['dups']==True])
# master_df.drop_duplicates(['state', 'parliamentary constituency '], inplace=True)



# merged=pd.merge(
#     ac_shp,
#     master_df,
#     left_on=['ST_NAME', 'PC_NAME'],
#     right_on=['state', 'parliamentary constituency '],
#     how='outer',
#     validate='1:1',

# )

# merged=gpd.GeoDataFrame(merged)

# merged.to_file(str(final_file), driver='ESRI Shapefile')
