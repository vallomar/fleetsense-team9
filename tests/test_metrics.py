import decimal, pathlib
import duckdb, pytest
from metrics import CHARGES_SQL, METRICS_SQL, assert_channel_complete
D=decimal.Decimal

def fixture():
 c=duckdb.connect()
 c.execute('''create table t(booking_channel varchar,fare_amount decimal(18,2),duration_minutes double,revenue_with_charges decimal(18,2),tolls_amount decimal(18,2),extra decimal(18,2),improvement_surcharge decimal(18,2),congestion_surcharge decimal(18,2),airport_fee decimal(18,2),cbd_congestion_fee decimal(18,2))''')
 c.execute("insert into t values ('hospital_booked',20,30,37,5,2,1,2,1,3),('street_hail',10,15,16,0,1,1,0,0,0)")
 c.execute(f'create view fact_trips as select *, {CHARGES_SQL} as charges, revenue_with_charges-({CHARGES_SQL}) as revenue_without_charges from t')
 return c

def test_cr1_exact_decimal():
 c=fixture(); assert c.execute('select sum(charges),sum(revenue_without_charges) from fact_trips').fetchone()==(D('16.00'),D('37.00'))

def test_channel_reconciliation():
 c=fixture(); r=c.execute(f'select {METRICS_SQL} from fact_trips').fetchone(); assert r[:4]==(2,1,1,0)
 assert_channel_complete(c)

def test_unknown_is_not_street():
 c=fixture(); c.execute("update t set booking_channel='unknown' where booking_channel='street_hail'")
 with pytest.raises(ValueError,match='lack authoritative'): assert_channel_complete(c)
 r=c.execute(f'select {METRICS_SQL} from fact_trips').fetchone(); assert r[:4]==(2,1,0,1)

def test_actual_row_balance():
 p=pathlib.Path(__file__).parents[1]/'data/warehouse.duckdb'
 if not p.exists(): pytest.skip('Run python run.py for full-data integration tests')
 c=duckdb.connect(str(p),read_only=True)
 assert c.execute('select bool_and(rows_in=rows_loaded+rows_quarantined),count(*) from ingestion_manifest').fetchone()==(True,12)
 assert c.execute('select sum(trips-hospital_booked_trips-street_hail_trips-unknown_channel_trips) from by_zone').fetchone()[0]==0
 assert c.execute('select sum(revenue_with_charges-revenue_without_charges-charges) from by_zone').fetchone()[0]==0
 assert c.execute('select count(*)-count(distinct (source_file,source_row)) from fact_trips').fetchone()[0]==0
