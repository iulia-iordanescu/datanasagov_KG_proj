# link_only.py -- print the public API link for one or more dataset ids, to
# open in a browser and read the dataset's full raw record. Builds the links
# only; it contacts nothing and works offline.
#
#
# Two example usages (first for getting the link of one specific dataset,
# the second for getting the link of multiple [example shows 3] specific datasets):
#   python link_only.py 13fb04bc-1158-4164-bd05-7d8adee340af
#   python link_only.py id1 id2 id3
import sys

for dataset_id in sys.argv[1:]:
    print(f"https://data.nasa.gov/api/3/action/package_show?id={dataset_id}")



#dataset_id refers to the id key, nested in the result key when you open the link. for example,
#opening https://data.nasa.gov/api/3/action/package_search?rows=1, you can see 
#id = c2b37e04-f1ab-44db-b85f-81732750d518
#so the link above could equivalently be replaced with
#https://data.nasa.gov/api/3/action/package_show?id=c2b37e04-f1ab-44db-b85f-81732750d518