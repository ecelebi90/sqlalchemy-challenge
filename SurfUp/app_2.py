# Import the dependencies.

import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///SurfUp/Resources/hawaii.sqlite")


# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def homepage():
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/&lt;start&gt;<br>" 
        f"/api/v1.0/&lt;start&gt/&lt;end&gt;" )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    most_recent_date = session.query(func.max(measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=366)
    results = session.query(measurement.date, measurement.prcp).filter(measurement.date >= one_year_ago).all()
    session.close()

    precipitation_dict = {date: prcp for date, prcp in results}
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(station.station).all()
    session.close()

    station_list = [station[0] for station in results]
    return jsonify(station_list)


@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    active_station =(session.query(measurement.station, func.count(measurement.station)).
                 group_by(measurement.station).
                 order_by(func.count(measurement.station).desc()).all())
    
    most_recent_date = session.query(func.max(measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=366)

    results = session.query(measurement.date, measurement.station, measurement.tobs).\
        filter(measurement.date >= one_year_ago).filter(measurement.station == 'USC00519281').all()
    session.close()
    
    temp_observations = []
    for date, station, tobs in results:
        temp_observations.append({
            "date": date,
            "station": station,
            "temperature": tobs })
    return jsonify(temp_observations)

@app.route("/api/v1.0/<start>") 
@app.route("/api/v1.0/<start>/<end>")
def temp_stats(start, end=None):
    session = Session(engine)

    if end:
        results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).\
            filter(measurement.date <= end).all()

    else:
        results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).all()
    session.close()

    temp_stats_data = []

    if results and len(results[0]) >= 3:
        temp_stats_data.append({
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
        })

        return jsonify(temp_stats_data)
    else:
        return jsonify({"error": "No temperature data found for the given date range."}), 404
    
if __name__=='__main__':
    app.run(debug=True)



           
