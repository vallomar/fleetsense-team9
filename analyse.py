"""Build six evidence charts from full 2025 TLC aggregates, never sampled."""
import pathlib, json
import duckdb, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).parent; OUT=ROOT/'reports'
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160,'axes.titlesize':13,'axes.labelsize':10})
c=duckdb.connect(str(ROOT/'data/warehouse.duckdb'),read_only=True)
queries={
'hour':"select hour(pickup_datetime) as bucket,count(*)/365.0 as trips from fact_trips group by 1 order by 1",
'weekday':"select isodow(pickup_datetime) as bucket,count(*)*1.0/(select count(*) from dim_calendar d where d.iso_weekday=isodow(f.pickup_datetime)) as trips from fact_trips f group by 1 order by 1",
'month':"select strftime(pickup_datetime,'%Y-%m') as bucket,count(*)*1.0/day(last_day(min(pickup_datetime))) as trips from fact_trips group by 1 order by 1",
'zones':"select z.LocationID as zone_id,z.Zone as zone,coalesce(b.trips,0) as trips,coalesce(b.charges,0) as charges,coalesce(b.revenue_with_charges,0) as gross from dim_zones z left join by_zone b on z.LocationID=b.zone_id where z.LocationID<=263 order by trips desc"
}
data={k:c.execute(q).df() for k,q in queries.items()}
for k,d in data.items(): d.to_csv(OUT/(k+'_chart_data.csv'),index=False)
def save(n,title,xlabel,ylabel):
 plt.title(title,loc='left',fontweight='bold',pad=16); plt.xlabel(xlabel); plt.ylabel(ylabel)
 plt.figtext(.02,.015,'Source: NYC TLC, Jan–Dec 2025. Accepted records only; booking channel unavailable.',fontsize=8,color='#475569')
 plt.tight_layout(rect=(0,.045,1,1)); plt.savefig(OUT/n); plt.close()
for k,desc in [('hour','Hour of day'),('weekday','ISO weekday'),('month','Month')]:
 d=data[k]; plt.figure(figsize=(9,4.4)); plt.bar(d.bucket.astype(str),d.trips,color='#2563eb');
 if k=='month': plt.xticks(rotation=40,ha='right')
 if k=='weekday': plt.xticks(range(7),['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
 save(k+'.png',desc+' seasonality, average accepted trips per day',desc,'Trips per day')
z=data['zones']
for name,d in [('top_zones',z.head(10).iloc[::-1]),('bottom_zones',z.sort_values(['trips','zone_id']).head(10).iloc[::-1])]:
 plt.figure(figsize=(9,5.3)); plt.barh(d.zone,d.trips,color='#2563eb'); save(name+'.png',name.replace('_',' ').title()+', full-year pickups','Accepted trips','Pickup zone')
d=z.sort_values('charges',ascending=False).head(10).iloc[::-1]; plt.figure(figsize=(9,5.3)); plt.barh(d.zone,d.charges/1e6,color='#0f766e'); save('charges.png','CR-1: largest toll and surcharge amounts by pickup zone','USD millions','Pickup zone')
summary={'peak_hour':int(data['hour'].loc[data['hour'].trips.idxmax(),'bucket']), 'peak_weekday_iso':int(data['weekday'].loc[data['weekday'].trips.idxmax(),'bucket']), 'top_zone':z.iloc[0].zone,'top_zone_trips':int(z.iloc[0].trips),'zero_trip_zones':int((z.trips==0).sum())}
(OUT/'analysis_summary.json').write_text(json.dumps(summary,indent=2)); print(summary)
