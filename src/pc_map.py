import pandas as pd
import geopandas as gpd
from pathlib import Path
from fuzzywuzzy import process


#defining directories
dir_path=Path(__file__).resolve().parents[1]
raw_data_path= dir_path.joinpath("data/raw")
external_data_path= dir_path.joinpath("data/external")
final_file=external_data_path.joinpath("final_map.shp")


#reading in the shape file
pc_shp_files=list(external_data_path.joinpath('pc_shp').glob("*.shp"))
pc_shp=gpd.read_file(str(pc_shp_files[0]))
# cleaning shape file
pc_shp['ST_NAME']=pc_shp['ST_NAME'].str.lower().str.strip()
pc_shp['PC_NAME']=pc_shp['PC_NAME'].str.lower().str.strip()



#reading in the master file
master_path=list(raw_data_path.glob("*.xlsx"))
master_df=pd.read_excel(master_path[0], sheet_name='master_list')

#susbetting for 2014
master_df=master_df[(master_df['year']==2014)&(master_df['election']=='Lok Sabha')&(master_df['internal_ac_pc']=='Yes')]
master_df['state']=master_df['state'].str.lower().str.strip()
master_df['parliamentary constituency ']=master_df['parliamentary constituency '].str.lower().str.strip()


master_df.drop_duplicates(['state', 'parliamentary constituency '], inplace=True)
master_df=master_df[['year', 'election', 'state', 'parliamentary constituency ']]
print(master_df.shape)
# master_df['dups']=master_df.duplicated(['state', 'parliamentary constituency '], keep=False)
# print(master_df['dups'].value_counts())



merged=pd.merge(
    pc_shp,
    master_df,
    left_on=['ST_NAME', 'PC_NAME'],
    right_on=['state', 'parliamentary constituency '],
    how='outer',
    validate='1:1',
    indicator=True

)

print(merged['_merge'].value_counts())

not_in_pc=merged[merged['_merge']=='right_only']['parliamentary constituency ']


# fuzzy matching

result=[process.extractOne(i, pc_shp['PC_NAME'])
        for i in not_in_pc]


result = pd.DataFrame(result, columns=["match", "score", "id"])
result.drop("id", axis=1, inplace=True)

mapper_df = pd.concat(
    [not_in_pc.reset_index(), result],
    axis=1,
    ignore_index=True,
    names=["original", "match", "score"],
)
# mapper_df = mapper_df[mapper_df[2] >= 90]


# creating a dictionary for fuzzy mapper
mapper_dict = dict(zip(mapper_df[1], mapper_df[2]))

# applying the mapper dictionary on the original processed state file to correct for fuzzy matched names
master_df["parliamentary constituency "] = master_df["parliamentary constituency "].replace(mapper_dict)
master_df['dups']=master_df.duplicated(['state', 'parliamentary constituency '], keep=False)
print(master_df[master_df['dups']==True])
master_df.drop_duplicates(['state', 'parliamentary constituency '], inplace=True)



merged=pd.merge(
    pc_shp,
    master_df,
    left_on=['ST_NAME', 'PC_NAME'],
    right_on=['state', 'parliamentary constituency '],
    how='outer',
    validate='1:1',

)

merged=gpd.GeoDataFrame(merged)

merged.to_file(str(final_file), driver='ESRI Shapefile')
