# coding: utf-8
import requests
import json
import folium

headers = {
       'AccountKey': 'qBE3CC9FS3C8PBq5TPzX7Q==', #avi account key
       'UniqueUserID': '8ecabd56-08a2-e843-0a7a-9944dccf124a', #avi pw
      'accept': 'application/json'
    }

def fetch_all(url):
    results = []
    while True:
        new_results = requests.get(
            url,
            headers=headers,
            params={'$skip': len(results)}
        ).json()['value']
        if new_results == []:
            break
        else:
            results += new_results
    return results


if __name__ == "__main__":
    # stops = fetch_all("http://datamall2.mytransport.sg/ltaodataservice/BusStops")
    # with open("stops.json", "w") as f:
    #     f.write(json.dumps(stops))
    stops = json.loads(open('C:\Users\IHL2016\PycharmProjects\/1008-DSA\stops.json').read())
    print len(stops)
    # services = fetch_all("http://datamall2.mytransport.sg/ltaodataservice/BusServices")
    # with open("services.json", "w") as f:
    #     f.write(json.dumps(services))
    services = json.loads(open('C:\Users\IHL2016\PycharmProjects\/1008-DSA\services.json').read())
    print len(services)
    # routes = fetch_all("http://datamall2.mytransport.sg/ltaodataservice/BusRoutes")
    # with open("routes.json", "w") as f:
    #     f.write(json.dumps(routes))
    routes = json.loads(open('C:\Users\IHL2016\PycharmProjects\/1008-DSA\/routes.json').read())
    print len(routes)