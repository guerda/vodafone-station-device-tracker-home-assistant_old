HTTP Requests to extract associated devices
===========================================


Login to API
------------

*Lookup request*
Request

    http://<ip>/api/v1/session/login

Body

    username=admin&password=seeksalthash

Cookie: `PHPSESSID`

Response:

    {"error":"ok","salt":"<11 character salt>","saltwebui":"<12 character salt>"}
    
    
*Login request*

The login token is generated via a salted hash. Fluepke did reverse engineered it here:
https://github.com/Fluepke/vodafone-station-exporter#reverse-engineering-the-login-mechanism

For Python, this is helpful: https://gist.github.com/tiberiucorbu/a51c81b82b5196ac002c52ac6f39987f#getting-the-encryption-salts

Body

    username=admin&password=<hash 32 characters>

Associated Devices
------------------

Request

    http://<ip>/api/v1/host/AssociatedDevices5?_=1674466341533

Cookie: `PHPSESSID`
    
Response
    
    {
       "error":"ok",
       "message":"all values retrieved",
       "data":{
          "AssociatedDevices5":[
             {
                "__id":"1",
                "macAddr":"7f-06-39-08-0c-1d",
                "linkRate":"6000",
                "features":"WNM "
             },
             {
                "__id":"2",
                "macAddr":"c3-56-1e-83-a6-20",
                "linkRate":"72222",
                "features":""
             }
          ]
       },
       "token":"<token with 64 characters, could be SHA256>"
    }
