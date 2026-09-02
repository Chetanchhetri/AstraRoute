# API Documentation

## Overview

This document describes the API endpoints defined in the supplied
Postman collections:

-   **OSRM Route Optimization API** --- health check, authentication,
    route optimization, and admin user management.
-   **Trip Planner** --- detailed trip planning.
-   **Disaster / Issue Reporting** --- active disaster lookup, issue reporting, and news scraping.

The Postman collections use `http://localhost:8000` as the default
`base_url`.

------------------------------------------------------------------------

## Base URL

``` text
http://localhost:8000
```

All endpoint paths below are relative to the base URL.

------------------------------------------------------------------------

# 1. Health API

## Health Check

Checks whether the API service is available.

**Method:** `GET`

**Endpoint:**

``` text
/health
```

**Authentication:** None

**Example request:**

``` bash
curl -X GET http://localhost:8000/health
```

------------------------------------------------------------------------

# 2. Authentication APIs

## Register User

Creates a regular user account.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/auth/register
```

**Authentication:** None

**Headers:**

``` http
Content-Type: application/json
```

**Request body:**

``` json
{
  "email": "user1@example.com",
  "password": "SecurePassword123!",
  "name": "Chetan Chhetri",
  "mobile_number": "+919876543210",
  "is_admin": false
}
```

### Fields

  -----------------------------------------------------------------------
  Field                   Type                    Description
  ----------------------- ----------------------- -----------------------
  `email`                 string                  User email address

  `password`              string                  User password

  `name`                  string                  User's name

  `mobile_number`         string                  User's mobile number

  `is_admin`              boolean                 Indicates whether the
                                                  account is an
                                                  administrator
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Login User

Authenticates a user.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/auth/login
```

**Authentication:** None

**Headers:**

``` http
Content-Type: application/json
```

**Request body:**

``` json
{
  "email": "user1@example.com",
  "password": "SecurePassword123!"
}
```

The Postman collection expects a successful response to contain an
`access_token`. The collection automatically stores this value in the
`access_token` collection variable.

------------------------------------------------------------------------

## Register Admin

Initiates administrator registration.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/auth/register/initiate
```

**Authentication:** None

**Headers:**

``` http
Content-Type: application/json
```

**Request body:**

``` json
{
  "email": "chhetrichetan45@gmail.com",
  "password": "Password123!",
  "name": "Chetan Chhetri",
  "mobile_number": "+918167680360",
  "is_admin": true
}
```

> The supplied Postman collection names this request **Register Admin**
> and sets `is_admin` to `true`.

------------------------------------------------------------------------

## Verify Admin Registration

Verifies the registration using an OTP.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/auth/register/verify
```

**Authentication:** None

**Request body:**

``` json
{
  "email": "chhetrichetan45@gmail.com",
  "otp": "123456"
}
```

The Postman request does not define an explicit `Content-Type` header
for this request, although its body is JSON-formatted.

------------------------------------------------------------------------

## Login Admin

Authenticates an administrator.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/auth/login
```

**Authentication:** None

**Headers:**

``` http
Content-Type: application/json
```

**Request body:**

``` json
{
  "email": "chhetrichetan45@gmail.com",
  "password": "Password123!"
}
```

On a successful response, the Postman collection stores the returned
`access_token` in the `admin_access_token` collection variable.

------------------------------------------------------------------------

# 3. Route Optimization API

## Optimize Route

Optimizes a route between a start point and an end point while
considering supplied stops.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/route/optimize
```

**Authentication:** Bearer token

**Authorization header:**

``` http
Authorization: Bearer {{access_token}}
```

**Headers:**

``` http
Content-Type: application/json
```

**Request body:**

``` json
{
  "start": {
    "latitude": 26.7132,
    "longitude": 88.4323,
    "name": "Siliguri"
  },
  "end": {
    "latitude": 26.7271,
    "longitude": 88.3953,
    "name": "Matigara"
  },
  "stops": [
    {
      "latitude": 26.6853,
      "longitude": 88.3247,
      "name": "Bagdogra"
    },
    {
      "latitude": 26.7587,
      "longitude": 88.4239,
      "name": "Sukna"
    }
  ],
  "round_trip": false
}
```

### Request fields

  -----------------------------------------------------------------------
  Field                   Type                    Description
  ----------------------- ----------------------- -----------------------
  `start`                 object                  Starting location

  `start.latitude`        number                  Starting latitude

  `start.longitude`       number                  Starting longitude

  `start.name`            string                  Starting location name

  `end`                   object                  Destination location

  `end.latitude`          number                  Destination latitude

  `end.longitude`         number                  Destination longitude

  `end.name`              string                  Destination name

  `stops`                 array                   Intermediate locations
                                                  to consider

  `stops[].latitude`      number                  Stop latitude

  `stops[].longitude`     number                  Stop longitude

  `stops[].name`          string                  Stop name

  `round_trip`            boolean                 Indicates whether the
                                                  route should be a round
                                                  trip
  -----------------------------------------------------------------------

### Example cURL

``` bash
curl -X POST http://localhost:8000/api/v1/route/optimize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "start": {
      "latitude": 26.7132,
      "longitude": 88.4323,
      "name": "Siliguri"
    },
    "end": {
      "latitude": 26.7271,
      "longitude": 88.3953,
      "name": "Matigara"
    },
    "stops": [
      {
        "latitude": 26.6853,
        "longitude": 88.3247,
        "name": "Bagdogra"
      },
      {
        "latitude": 26.7587,
        "longitude": 88.4239,
        "name": "Sukna"
      }
    ],
    "round_trip": false
  }'
```

------------------------------------------------------------------------

# 4. Admin APIs

## List All Users

Returns the users available through the admin users endpoint.

**Method:** `GET`

**Endpoint:**

``` text
/api/v1/admin/users
```

**Authentication:** Bearer token using the admin access token.

**Authorization header:**

``` http
Authorization: Bearer {{admin_access_token}}
```

### Example cURL

``` bash
curl -X GET http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN"
```

------------------------------------------------------------------------

# 5. Disaster / Issue Reporting APIs

## Show Active Disasters

Returns the currently active disasters.

**Method:** `GET`

**Endpoint:**

``` text
/api/v1/disasters/active
```

**Authentication:** None

### Example cURL

``` bash
curl -X GET http://localhost:8000/api/v1/disasters/active
```

------------------------------------------------------------------------

## Report Issue

Reports a disaster or road issue at a specified geographic location.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/disasters/report
```

**Authentication:** None

**Request body:**

``` json
{
  "disaster_type": "Landslide",
  "description": "Mudslide blocking road near Matigara.",
  "latitude": 26.7132,
  "longitude": 88.4323,
  "radius_km": 1.0,
  "duration_hours": 12
}
```

### Request fields

| Field | Type | Description |
|---|---|---|
| `disaster_type` | string | Type of disaster or issue being reported |
| `description` | string | Description of the reported issue |
| `latitude` | number | Latitude of the affected location |
| `longitude` | number | Longitude of the affected location |
| `radius_km` | number | Radius of the affected area in kilometres |
| `duration_hours` | number | Expected duration of the reported issue in hours |

### Example cURL

``` bash
curl -X POST http://localhost:8000/api/v1/disasters/report \
  -H "Content-Type: application/json" \
  -d '{
    "disaster_type": "Landslide",
    "description": "Mudslide blocking road near Matigara.",
    "latitude": 26.7132,
    "longitude": 88.4323,
    "radius_km": 1.0,
    "duration_hours": 12
  }'
```

------------------------------------------------------------------------

## Scrape News

Triggers disaster/news scraping.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/disasters/scrape-news
```

**Authentication:** Bearer token

**Authorization header:**

``` http
Authorization: Bearer {{json_web_token_0g6f}}
```

### Example cURL

``` bash
curl -X POST http://localhost:8000/api/v1/disasters/scrape-news \
  -H "Authorization: Bearer YOUR_JSON_WEB_TOKEN"
```

> The supplied Postman collection uses the collection variable
> `json_web_token_0g6f` for this request. The variable is marked as secret.

------------------------------------------------------------------------

# 6. Trip Planner API

## Plan Detailed Trip

Creates a detailed trip plan using a start location, destination, travel
preferences, and optional avoidance areas.

**Method:** `POST`

**Endpoint:**

``` text
/api/v1/trip/plan
```

**Authentication:** Bearer token

**Authorization header:**

``` http
Authorization: Bearer {{access_token}}
```

**Headers:**

``` http
Content-Type: application/json
```

**Request body:**

``` json
{
  "start": {
    "latitude": 26.7132,
    "longitude": 88.4323,
    "name": "Siliguri"
  },
  "end": {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "name": "Delhi"
  },
  "preferences": {
    "travel_mode": "driving",
    "trip_pace": "balanced",
    "max_detour_km": 30.0,
    "interests": [
      "heritage",
      "spiritual"
    ],
    "include_petrol_pumps": true,
    "include_ev_chargers": false,
    "include_hotels": true,
    "include_restaurants": true,
    "include_attractions": true,
    "budget_level": "medium"
  },
  "avoid_boxes": []
}
```

### Request fields

  ------------------------------------------------------------------------------------
  Field                                Type                    Description
  ------------------------------------ ----------------------- -----------------------
  `start`                              object                  Starting location

  `start.latitude`                     number                  Starting latitude

  `start.longitude`                    number                  Starting longitude

  `start.name`                         string                  Starting location name

  `end`                                object                  Destination location

  `end.latitude`                       number                  Destination latitude

  `end.longitude`                      number                  Destination longitude

  `end.name`                           string                  Destination name

  `preferences`                        object                  Trip planning
                                                               preferences

  `preferences.travel_mode`            string                  Travel mode; the
                                                               supplied request uses
                                                               `driving`

  `preferences.trip_pace`              string                  Trip pace; the supplied
                                                               request uses `balanced`

  `preferences.max_detour_km`          number                  Maximum detour distance
                                                               in kilometres

  `preferences.interests`              array                   Areas of interest;
                                                               supplied values are
                                                               `heritage` and
                                                               `spiritual`

  `preferences.include_petrol_pumps`   boolean                 Whether to include
                                                               petrol pumps

  `preferences.include_ev_chargers`    boolean                 Whether to include EV
                                                               chargers

  `preferences.include_hotels`         boolean                 Whether to include
                                                               hotels

  `preferences.include_restaurants`    boolean                 Whether to include
                                                               restaurants

  `preferences.include_attractions`    boolean                 Whether to include
                                                               attractions

  `preferences.budget_level`           string                  Budget level; the
                                                               supplied request uses
                                                               `medium`

  `avoid_boxes`                        array                   Avoidance areas;
                                                               supplied request
                                                               contains an empty array
  ------------------------------------------------------------------------------------

### Example cURL

``` bash
curl -X POST http://localhost:8000/api/v1/trip/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "start": {
      "latitude": 26.7132,
      "longitude": 88.4323,
      "name": "Siliguri"
    },
    "end": {
      "latitude": 28.6139,
      "longitude": 77.2090,
      "name": "Delhi"
    },
    "preferences": {
      "travel_mode": "driving",
      "trip_pace": "balanced",
      "max_detour_km": 30.0,
      "interests": [
        "heritage",
        "spiritual"
      ],
      "include_petrol_pumps": true,
      "include_ev_chargers": false,
      "include_hotels": true,
      "include_restaurants": true,
      "include_attractions": true,
      "budget_level": "medium"
    },
    "avoid_boxes": []
  }'
```

------------------------------------------------------------------------

# 7. Endpoint Summary

  Category         Method   Endpoint                           Authentication
  ---------------- -------- ---------------------------------- --------------------
  Health           GET      `/health`                          None
  Authentication   POST     `/api/v1/auth/register`            None
  Authentication   POST     `/api/v1/auth/login`               None
  Authentication   POST     `/api/v1/auth/register/initiate`   None
  Authentication   POST     `/api/v1/auth/register/verify`     None
  Authentication   POST     `/api/v1/auth/login`               None
  Routes           POST     `/api/v1/route/optimize`           User Bearer token
  Admin            GET      `/api/v1/admin/users`              Admin Bearer token
  Trip Planner     POST     `/api/v1/trip/plan`                User Bearer token

------------------------------------------------------------------------

# 8. Postman Variables

The supplied collections define the following variables.

## OSRM Route Optimization API

  Variable               Default value             Purpose
  ---------------------- ------------------------- ------------------------------------
  `base_url`             `http://localhost:8000`   API base URL
  `access_token`         empty                     User authentication token
  `admin_access_token`   empty                     Administrator authentication token

## Disaster / Issue Reporting

   Variable               Default value             Purpose
   ---------------------- ------------------------- ------------------------------------
   `json_web_token_0g6f`  secret                    Bearer token for `/api/v1/disasters/scrape-news`

## Trip Planner

  Variable         Default value             Purpose
  ---------------- ------------------------- ---------------------------
  `base_url`       `http://localhost:8000`   API base URL
  `access_token`   empty                     User authentication token

------------------------------------------------------------------------

# 9. Authentication Flow

A typical authenticated request flow based on the supplied Postman
collections is:

1.  Register a user using `/api/v1/auth/register`.
2.  Login using `/api/v1/auth/login`.
3.  Store the returned `access_token`.
4.  Send the token as a Bearer token when calling protected endpoints
    such as:
    -   `/api/v1/route/optimize`
    -   `/api/v1/trip/plan`

For administrator operations:

1.  Initiate admin registration using `/api/v1/auth/register/initiate`.
2.  Verify registration using `/api/v1/auth/register/verify`.
3.  Login using `/api/v1/auth/login`.
4.  Store the returned token as `admin_access_token`.
5.  Use that token for `/api/v1/admin/users`.

------------------------------------------------------------------------

# 10. Scope and Limitations

This documentation is generated directly from the supplied Postman
collections. The collections do **not** contain response examples,
response schemas, HTTP status-code documentation, or detailed
server-side validation rules. Therefore, those details are intentionally
not specified here.

The documentation describes the routes, methods, authentication
configuration, variables, and request payloads that are actually present
in the supplied collections.
