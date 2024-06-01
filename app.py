from flask import Flask, request, render_template

import heapq
import argparse
import sqlite3
import os

app = Flask(__name__)

@app.route('/')
def index():
    result = "Waiting for inputs"
    return render_template('index.html', path=result)


class PatrolRoute:
    def __init__(self):
        self.crime = {
            'Mattar': 49,
            'MacPherson': 70,
            'Ubi': 43,
            'Kaki Bukit': 71,
            'Bedok North': 87,
            'Bedok Reservoir': 70,
            'Tampines West': 20,
            'Tampines': 19,
            'Tampines East': 7,
            'Upper Changi': 24,
            'Expo': 39,
            'Paya Lebar': 57,
            'Aljunied': 99,
            'Kallang': 1,
            'Eunos': 45,
            'Kembangan': 14,
            'Bedok': 54,
            'Tanah Merah': 7,
            'Simei': 26,
            'Pasir Ris': 20,
            'Dakota': 67,
            'Mountbatten': 33,
            'Stadium': 32
        }

        self.trainNetwork = {
            # Down-Town Line (DTL)
            'Mattar' : {'MacPherson' : 2},
            'MacPherson' : {'Mattar' : 2, 'Ubi' : 2, 'Paya Lebar': 2},
            'Ubi' : {'MacPherson' : 2, 'Kaki Bukit' : 2},
            'Kaki Bukit' : {'Ubi' : 2, 'Bedok North' : 2},
            'Bedok North' : {'Kaki Bukit' : 2, 'Bedok Reservoir' : 2},
            'Bedok Reservoir' : {'Bedok North' : 2, 'Tampines West' : 2},
            'Tampines West' : {'Bedok Reservoir' : 2, 'Tampines' : 2},
            'Tampines' : {'Tampines West' : 2, 'Tampines East' : 2, 'Simei' : 2, 'Pasir Ris' : 3},
            'Tampines East' : {'Tampines' : 2, 'Upper Changi' : 3},
            'Upper Changi' : {'Tampines East' : 3, 'Expo' : 2},
            'Expo' : {'Upper Changi' : 2},
            
            #East-West Line (EWL)
            'Paya Lebar' : {'MacPherson' : 2, 'Aljunied' : 2, 'Dakota' : 2, 'Eunos' : 2},
            'Aljunied' : {'Paya Lebar' : 2, 'Kallang' : 2},
            'Kallang' : {'Aljunied' : 2},
            'Eunos' : {'Paya Lebar' : 2, 'Kembangan' : 2},
            'Kembangan' : {'Eunos' : 2, 'Bedok' : 2},
            'Bedok' : {'Kembangan' : 2, 'Tanah Merah' : 3},
            'Tanah Merah' : {'Bedok' : 3, 'Simei' : 3},
            'Simei' : {'Tampines' : 2, 'Tanah Merah' : 3},
            'Pasir Ris' : {'Tampines' : 3},
            
            #Circle Line (CCL)
            'Dakota' : {'Paya Lebar' : 2, 'Mountbatten' : 2},
            'Mountbatten' : {'Dakota' : 2, 'Stadium' : 2},
            'Stadium' : {'Mountbatten' : 2}
            
            
        }

        self.db_file = "session_state.db"
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_state (
                station TEXT PRIMARY KEY,
                visit_count INTEGER
            )
        ''')
        for station in self.crime:
            cursor.execute('''
                INSERT OR IGNORE INTO session_state (station, visit_count)
                VALUES (?, 0)
            ''', (station,))
        conn.commit()
        conn.close()

    def get_visit_count(self, station):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT visit_count FROM session_state WHERE station = ?', (station,))
        visit_count = cursor.fetchone()[0]
        conn.close()
        return visit_count

    def increment_visit_count(self, station):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('UPDATE session_state SET visit_count = visit_count + 1 WHERE station = ?', (station,))
        conn.commit()
        conn.close()

    def reset_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM session_state')
        for station in self.crime:
            cursor.execute('''
                INSERT INTO session_state (station, visit_count)
                VALUES (?, 0)
            ''', (station,))
        conn.commit()
        conn.close()

    def timeTaken(self, station1, station2):
        queue = [(0, station1)]  # Priority queue with (travel_time, station)
        times = {station: float('inf') for station in self.trainNetwork}
        times[station1] = 0
        visited = set()

        while queue:
            current_time, current_station = heapq.heappop(queue)
            
            if current_station in visited:
                continue
            
            visited.add(current_station)
            
            if current_station == station2:
                return current_time
            
            for neighbor, travel_time in self.trainNetwork[current_station].items():
                time = current_time + travel_time
                if time < times[neighbor]:
                    times[neighbor] = time
                    heapq.heappush(queue, (time, neighbor))
        
        return float('inf')  # In case there is no path from start to end

    def findNextStation(self, notVisited, currentStation):
        tempStation = notVisited[0]
        steepestGradient = 0
        for station in notVisited:
            visit_count = self.get_visit_count(station)
            if visit_count == 0:
                visit_count = 1  # To avoid division by zero

            tempGradient = ((self.timeTaken(station, currentStation)) * 2 + (self.crime[station] / visit_count) * 2) * 0.5
            if tempGradient > steepestGradient:
                steepestGradient = tempGradient
                tempStation = station
        
        return tempStation

    def patrolRoute(self, stationsToPatrol, startingStation):
        res = []  # res will be the stations to visit in order
        notVisited = list(self.crime.keys())

        res.append(startingStation)
        notVisited.remove(startingStation)
        stationsToPatrol -= 1   
        self.increment_visit_count(startingStation)

        while stationsToPatrol > 0 and notVisited:
            nextStation = self.findNextStation(notVisited, res[-1])
            notVisited.remove(nextStation)
            res.append(nextStation)
            stationsToPatrol -= 1
            self.increment_visit_count(nextStation)

        #print("Session State:")
        self.print_session_state()  # Print session state for debugging
        return res

    def print_session_state(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM session_state')
        session_state = cursor.fetchall()
        # for station, count in session_state:
        #     print(f"{station}: {count}")
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Calculate patrol route for maximum crime stations.')
    parser.add_argument('--stationsToPatrol', type=int, help='Number of stations to patrol')
    parser.add_argument('--startingStation', type=str, nargs='+', help='Starting station name')
    parser.add_argument('--reset', action='store_true', help='Reset the session state database')
    args = parser.parse_args()

    patrol_route = PatrolRoute()

    if args.reset:
        patrol_route.reset_db()
        print("Database has been reset.")
    elif args.stationsToPatrol and args.startingStation:
        starting_station = ' '.join(args.startingStation)
        result = patrol_route.patrolRoute(args.stationsToPatrol, starting_station)
        print(result)
    else:
        print("Please provide both stationsToPatrol and startingStation, or use --reset to reset the database.")

if __name__ == "__main__":
    main()

@app.route('/', methods=['POST'])
def getValue():
    patrol_route = PatrolRoute()

    stationsToPatrol = int(request.form['numberOfStations'])
    startingStation = request.form['startingStation']
    result = patrol_route.patrolRoute(stationsToPatrol, startingStation)
    return render_template('index.html', path=result)


if __name__ == '__main__':
    app.run(debug=True)