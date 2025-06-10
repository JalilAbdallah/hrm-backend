# Cases API Documentation

This document provides an overview of the API endpoints for managing cases in the Human Rights Monitor (HRM) system.

## Base URL

All endpoints are prefixed with `/cases`.

## Authentication

Authentication is handled by a separate service and is not detailed in this document. Ensure that appropriate authentication headers are included in your requests.

## Visualizations

Visualizations can be generated based on the data returned by these endpoints. For example, a map visualization can show the geographical distribution of cases, and charts can represent case statuses or trends over time.

## Endpoints

---

### 1. List Active Cases

*   **Endpoint:** `GET /`
*   **Description:** Retrieves a paginated list of active cases. Supports filtering by various criteria.
*   **URL Parameters (Query Parameters):**
    *   `violation_types` (optional, string): Filter cases by a comma-separated list of violation types (e.g., "torture,illegal detention"). Cases matching all specified types will be returned.
    *   `status` (optional, string): Filter cases by status (e.g., "open", "closed", "under_investigation").
    *   `country` (optional, string): Filter cases by country.
    *   `region` (optional, string): Filter cases by region.
    *   `priority` (optional, string): Filter cases by priority level (e.g., "low", "medium", "high").
    *   `search` (optional, string): Search term for case title or description.
    *   `date_from` (optional, string, `YYYY-MM-DD`): Filter cases created on or after this date.
    *   `date_to` (optional, string, `YYYY-MM-DD`): Filter cases created on or before this date.
    *   `skip` (optional, integer, default: 0): Number of cases to skip for pagination.
    *   `limit` (optional, integer, default: 100, max: 500): Maximum number of cases to return.
*   **Returns:**
    *   `200 OK`: A JSON object containing:
        *   `cases`: A list of case objects.
        *   `pagination`: An object with pagination details (`total_count`, `current_skip`, `current_limit`, `returned_count`, `has_next`, `has_prev`).
        *   `filters_applied`: An object showing the filters used in the request.
    *   `400 Bad Request`: If date parameters are invalid.
    *   `500 Internal Server Error`: If there's a server-side issue.
*   **Example Success Response (200 OK):**
    ```json
    {
        "cases": [
            {
                "_id": "60d5ecf8b392f8a7b8c4d5e1",
                "case_id": "HRM-2023-4001",
                "title": "Case Title 1",
                "description": "Description of the case.",
                "violation_types": ["torture", "illegal detention"],
                "status": "open",
                "priority": "high",
                "location": {
                    "country": "CountryX",
                    "region": "RegionY",
                    "city": "CityZ"
                },
                "created_by": "user_id_123",
                "created_at": "2023-01-15T10:00:00Z",
                "updated_at": "2023-01-20T14:30:00Z"
                // ... other case fields
            }
        ],
        "pagination": {
            "total_count": 50,
            "current_skip": 0,
            "current_limit": 100,
            "returned_count": 1,
            "has_next": false,
            "has_prev": false
        },        "filters_applied": {
            "violation_types": "torture,illegal detention",
            "status": "open",
            "country": "CountryX",
            "region": null,
            "priority": "high",
            "search": null,
            "date_from": "2023-01-01",
            "date_to": "2023-12-31"
        }
    }
    ```

---

### 2. Get Single Case by ID

*   **Endpoint:** `GET /{case_id}`
*   **Description:** Retrieves a single active case by its unique ID.
*   **URL Parameters (Path Parameter):**
    *   `case_id` (required, string): The MongoDB ObjectId of the case.
*   **Returns:**
    *   `200 OK`: A JSON object representing the case.
    *   `400 Bad Request`: If `case_id` is invalid.
    *   `404 Not Found`: If the case with the given ID is not found.
    *   `500 Internal Server Error`: If there's a server-side issue.
*   **Example Success Response (200 OK):**
    ```json
    {
        "_id": "60d5ecf8b392f8a7b8c4d5e1",
        "case_id": "HRM-2023-4001",
        "title": "Case Title 1",
        "description": "Description of the case.",
        // ... other case fields
    }
    ```

---

### 3. Create New Case

*   **Endpoint:** `POST /`
*   **Description:** Creates a new case.
*   **Request Body:** A JSON object representing the case data. See [Request Body Formats](#request-body-formats) for `case_data` structure.
*   **Returns:**
    *   `200 OK`: A JSON object with a success message and the created case.
        ```json
        {
            "message": "Case created successfully",
            "case": { /* created case object */ }
        }
        ```
    *   `400 Bad Request`: If required fields are missing or data is invalid.
    *   `500 Internal Server Error`: If there's a server-side issue.

---

### 4. Update Existing Case

*   **Endpoint:** `PATCH /{case_id}`
*   **Description:** Updates an existing case. Allows partial updates. Can update multiple fields including status, victims, and source_reports.
*   **URL Parameters (Path Parameter):**
    *   `case_id` (required, string): The MongoDB ObjectId of the case to update.
*   **Request Body:** A JSON object. See [Request Body Formats](#request-body-formats) for `CaseUpdateRequest` structure.
*   **Returns:**
    *   `200 OK`: A JSON object with a success message and the updated case.
        ```json
        {
            "message": "Case updated successfully",
            "case": { /* updated case object */ }
        }
        ```
    *   `400 Bad Request`: If `case_id` or request data is invalid (e.g., missing `updated_by` when updating status).
    *   `404 Not Found`: If the case with the given ID is not found.
    *   `500 Internal Server Error`: If there's a server-side issue.

---

### 5. Archive Case (Soft Delete)

*   **Endpoint:** `DELETE /{case_id}`
*   **Description:** Moves a case from the active collection to the archived cases collection (soft delete).
*   **URL Parameters (Path Parameter):**
    *   `case_id` (required, string): The MongoDB ObjectId of the case to archive.
*   **Returns:**
    *   `200 OK`: A JSON object with a success message.
        ```json
        {
            "message": "Case archived successfully"
        }
        ```
    *   `400 Bad Request`: If `case_id` is invalid.
    *   `404 Not Found`: If the case with the given ID is not found in the active collection.
    *   `500 Internal Server Error`: If there's a server-side issue.

---

### 6. List Archived Cases

*   **Endpoint:** `GET /archive/`
*   **Description:** Retrieves a paginated list of archived cases. Supports the same filtering options as listing active cases.
*   **URL Parameters (Query Parameters):**
    *   Same as [List Active Cases](#1-list-active-cases).
        *   Note: `violation_types` should be a comma-separated string if filtering by multiple types.
*   **Returns:**
    *   `200 OK`: A JSON object similar to the response for [List Active Cases](#1-list-active-cases), but containing archived cases.
    *   `400 Bad Request`: If date parameters are invalid.
    *   `500 Internal Server Error`: If there's a server-side issue.

---

### 7. Get Single Archived Case by ID

*   **Endpoint:** `GET /archive/{case_id}`
*   **Description:** Retrieves a single archived case by its unique ID.
*   **URL Parameters (Path Parameter):**
    *   `case_id` (required, string): The MongoDB ObjectId of the archived case.
*   **Returns:**
    *   `200 OK`: A JSON object representing the archived case.
    *   `400 Bad Request`: If `case_id` is invalid.
    *   `404 Not Found`: If the archived case with the given ID is not found.
    *   `500 Internal Server Error`: If there's a server-side issue.

---

### 8. Restore Archived Case

*   **Endpoint:** `POST /archive/{case_id}/restore`
*   **Description:** Moves an archived case back to the active cases collection.
*   **URL Parameters (Path Parameter):**
    *   `case_id` (required, string): The MongoDB ObjectId of the case to restore.
*   **Returns:**
    *   `200 OK`: A JSON object with a success message and the `case_id` of the restored case.
        ```json
        {
            "message": "Case restored successfully",
            "case_id": "60d5ecf8b392f8a7b8c4d5e1"
        }
        ```
    *   `400 Bad Request`: If `case_id` is invalid.
    *   `404 Not Found`: If the case with the given ID is not found in the archived collection.
    *   `500 Internal Server Error`: If there's a server-side issue.

---

### 9. Get Case Status History

*   **Endpoint:** `GET /history/{case_id}`
*   **Description:** Retrieves the status change history for a specific case.
*   **URL Parameters (Path Parameter):**
    *   `case_id` (required, string): The `case_id` (e.g., "HRM-2023-4001", **not** the MongoDB `_id`) of the case.
*   **Returns:**
    *   `200 OK`: A JSON array containing history entries. Each entry includes the status, timestamp of the change, and the user who made the update.
        ```json
        [
            {
                "status": "new",
                "updated_at": "2023-01-15T10:00:00Z",
                "updated_by": "user_id_123"
            },
            {
                "status": "open",
                "updated_at": "2023-01-16T11:00:00Z",
                "updated_by": "user_id_456"
            }
        ]
        ```
    *   `400 Bad Request`: If `case_id` is invalid (note: this refers to the custom `case_id` string, not the MongoDB `_id`).
    *   `404 Not Found`: If history for the given `case_id` is not found.
    *   `500 Internal Server Error`: If there's a server-side issue.

---

## Request Body Formats

### 1. `CaseFilters` (Used as Query Parameters for GET requests)

This schema defines the available query parameters for filtering lists of cases (both active and archived).

```json
{
    "violation_types": "string (optional, comma-separated for multiple values)",
    "status": "string (optional)",
    "country": "string (optional)",
    "region": "string (optional)",
    "priority": "string (optional)",
    "search": "string (optional)",
    "date_from": "string (optional, YYYY-MM-DD)",
    "date_to": "string (optional, YYYY-MM-DD)",
    "skip": "integer (optional, default: 0, min: 0)",
    "limit": "integer (optional, default: 100, min: 1, max: 500)"
}
```
**Field Descriptions:**
*   `violation_types`: Filter by a specific type or a comma-separated list of violation types. If multiple types are provided, cases matching all of them will be returned.
*   `status`: Filter by case status (e.g., "open", "closed", "under_investigation").
*   `country`: Filter by the country where the case occurred.
*   `region`: Filter by the region within the country.
*   `priority`: Filter by case priority level (e.g., "low", "medium", "high").
*   `search`: Search term for case title or description.
*   `date_from`: Start date for filtering cases by their creation date.
*   `date_to`: End date for filtering cases by their creation date.
*   `skip`: Number of records to skip (for pagination).
*   `limit`: Maximum number of records to return in one request.

### 2. `case_data` (for `POST /`)

This is a flexible dictionary used when creating a new case.
**Required Fields:**
*   `title` (string): The title or name of the case.
*   `description` (string): A detailed description of the case.
*   `violation_types` (array of strings): A list of violation types associated with the case (e.g., `["torture", "enforced disappearance"]`).
*   `priority` (string): The priority level of the case (e.g., "high", "medium", "low").
*   `location` (object): An object detailing the location of the incident.
    *   `country` (string, required): The country where the incident occurred.
    *   `region` (string, optional): The region or state.
    *   `city` (string, optional): The city or town.
    *   `address_line_1` (string, optional): Specific address details.
    *   `latitude` (float, optional): Latitude coordinate.
    *   `longitude` (float, optional): Longitude coordinate.
*   `created_by` (string, MongoDB ObjectId): The ID of the user creating the case.

**Optional Fields:**
*   `status` (string, defaults to "new"): The initial status of the case.
*   `source_reports` (string or array of strings, MongoDB ObjectIds): ID(s) of source reports linked to this case. Can be a single ObjectId string or an array of ObjectId strings.
*   `victims` (string or array of strings, MongoDB ObjectIds): ID(s) of individuals identified as victims. Can be a single ObjectId string or an array of ObjectId strings.
*   Any other relevant fields for the case.

**Example `case_data` for `POST /` (with arrays):**
```json
{
    "title": "Unlawful Arrest and Detention of Activist",
    "description": "Prominent human rights activist John Doe was arrested without a warrant on June 1, 2025, and has been held incommunicado since.",
    "violation_types": ["illegal detention", "denial of due process"],
    "priority": "high",
    "location": {
        "country": "Freedonia",
        "region": "North Province",
        "city": "Capital City"
    },
    "created_by": "60d5ecf8b392f8a7b8c4d5a0",
    "source_reports": ["60d5ecf8b392f8a7b8c4d5b1", "60d5ecf8b392f8a7b8c4d5b2"],
    "victims": ["60d5ecf8b392f8a7b8c4d5c3"]
}
```

**Example `case_data` for `POST /` (with single values):**
```json
{
    "title": "Individual Report Case",
    "description": "Case created from a single incident report.",
    "violation_types": ["torture"],
    "priority": "high",
    "location": {
        "country": "Freedonia",
        "region": "South Province",
        "city": "Border Town"
    },
    "created_by": "60d5ecf8b392f8a7b8c4d5a0",
    "source_reports": "60d5ecf8b392f8a7b8c4d5b1",
    "victims": "60d5ecf8b392f8a7b8c4d5c3"
}
```

### 3. `CaseUpdateRequest` (for `PATCH /{case_id}`)

This schema is used for updating an existing case.

```json
{
    "case_data": {
        "status": "string (optional)",
        "victims": "array of strings (MongoDB ObjectIds, optional)",
        "source_reports": "array of strings (MongoDB ObjectIds, optional)",
        "updated_by": "string (MongoDB ObjectId, required when updating status)"
    }
}
```
**Field Descriptions:**
*   `case_data` (object, required):
    *   `status` (string, optional): The new status for the case (e.g., "open", "closed", "under_investigation"). If provided, `updated_by` is mandatory.
    *   `victims` (array of strings, MongoDB ObjectIds, optional): A list of victim IDs to associate with the case. This will replace the existing list of victims.
    *   `source_reports` (array of strings, MongoDB ObjectIds, optional): A list of source report IDs to associate with the case. This will replace the existing list of source reports.
    *   `updated_by` (string, MongoDB ObjectId, required when updating status): The ID of the user performing the update. This is required when updating the status field.

**Example `CaseUpdateRequest` for `PATCH /{case_id}`:**
```json
{
    "case_data": {
        "status": "under_investigation",
        "victims": ["60d5ecf8b392f8a7b8c4d5c3", "60d5ecf8b392f8a7b8c4d5d4"],
        "source_reports": ["60d5ecf8b392f8a7b8c4d5b1", "60d5ecf8b392f8a7b8c4d5b2"],
        "updated_by": "60d5ecf8b392f8a7b8c4d5a0"
    }
}
```
**Note on `PATCH` behavior:**
*   Fields that can be updated: `status`, `victims`, and `source_reports`.
*   If `status` is being updated, the `updated_by` field is mandatory and will be recorded in the case's history.
*   Updating `victims` or `source_reports` will overwrite the entire existing list with the new list provided.
*   Valid status values are: "open", "closed", "under_investigation".

---
