## Forecast API

This endpoint allows users to submit forecasting data for analysis and visualization. It processes the provided input and returns a structured response containing the forecast plot data.

### Request

**Method:** POST  
**URL:** `https://forecast-7na0.onrender.com/forecast`

#### Request Body

The request body must be sent as `form-data` and should include the following parameters:

- **file** (type: file): A file containing the data necessary for forecasting.
    
- **country** (type: text): The country for which the forecast is being generated.
    
- **tech** (type: text): The technology type relevant to the forecast.
    
- **zone** (type: text): The geographical zone associated with the forecast.
    
- **kpi** (type: text): Key Performance Indicator relevant to the forecast.
    

### Response

Upon successful processing of the request, the API will return a response with a status code of `200` and a content type of `application/json`.

#### Response Format

The response will include a JSON object with the following structure:

- **plot**: Contains the data and layout for the forecast visualization.
    
    - **data**: An array of objects representing different plot types, each with properties such as `mode`, `name`, `type`, `x`, and `y`.
        
    - **layout**: An object that defines the layout settings for the plot, including axes, title, and other visual attributes.
        

The specific details of the plot data will depend on the input provided in the request.

### Example Response

``` json
{
  "plot": {
    "data": [
      {
        "mode": "",
        "name": "",
        "type": "",
        "x": [""],
        "y": {
          "bdata": "",
          "dtype": ""
        }
      }
    ],
    "layout": {
      "template": {
        "data": {
          "bar": [{"error_x": {"color": ""}, "error_y": {"color": ""}, "marker": {"line": {"color": "", "width": 0},"pattern": {"fillmode": "", "size": 0, "solidity": 0}}, "type": ""}],
          ...
        },
        "layout": {
          ...
        }
      },
      "title": {"text": ""},
      ...
    },
    "summary": ""
  }
}

 ```

This response structure allows clients to easily interpret and visualize the forecast data based on the parameters submitted.


#### Request Body (form-data)

| Key             | Type   | Example Value                                                                 |
|------------------|--------|---------------------------------------------------------------------------------|
| `file`          | File   | `/C:/Users/Naman Sharma/Desktop/AI_USE_CASES/generated_files_300_corrected.zip` |
| `country`       | Text   | `Benin`                                                                         |
| `tech`          | Text   | `2G`                                                                             |
| `zone`          | Text   | `Zone 1`                                                                         |
| `kpi`           | Text   | `HTTP Session Setup duration`                                                   |
| `forecast_months` | Text | `3` (optional; default is 3)                                                    |

