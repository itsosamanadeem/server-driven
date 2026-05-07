# `arch_json` Schema Specification
### Server-Driven UI Platform — View Definition Contract
**Version:** 1.0  
**Last Updated:** 2026-05-06

---

## Table of Contents

1. [Overview](#1-overview)
2. [Top-Level View Object](#2-top-level-view-object)
3. [View Types](#3-view-types)
4. [Actions](#4-actions)
5. [Components](#5-components)
   - 5.1 [field](#51-field)
   - 5.2 [group](#52-group)
   - 5.3 [tabs / tab](#53-tabs--tab)
   - 5.4 [notebook](#54-notebook)
   - 5.5 [separator](#55-separator)
   - 5.6 [html](#56-html)
6. [Widget Catalogue](#6-widget-catalogue)
   - 6.1 [char](#61-char)
   - 6.2 [integer](#62-integer)
   - 6.3 [float](#63-float)
   - 6.4 [boolean](#64-boolean)
   - 6.5 [date](#65-date)
   - 6.6 [datetime](#66-datetime)
   - 6.7 [text](#67-text)
   - 6.8 [selection](#68-selection)
   - 6.9 [many2one](#69-many2one)
   - 6.10 [one2many](#610-one2many)
   - 6.11 [many2many](#611-many2many)
   - 6.12 [file](#612-file)
   - 6.13 [monetary](#613-monetary)
   - 6.14 [badge](#614-badge)
   - 6.15 [progress](#615-progress)
7. [Filter Bar (List Views)](#7-filter-bar-list-views)
8. [Server Enrichment](#8-server-enrichment)
9. [Field-Level Access Rules](#9-field-level-access-rules)
10. [Complete Examples](#10-complete-examples)
    - 10.1 [Employee Form View](#101-employee-form-view)
    - 10.2 [Employee List View](#102-employee-list-view)
11. [Validation Rules](#11-validation-rules)
12. [Versioning](#12-versioning)
13. [Frontend Renderer Contract](#13-frontend-renderer-contract)

---

## 1. Overview

`arch_json` is the **view definition language** of this platform. It is a JSON object stored per view in `ir_view.arch_json` and returned — enriched with field metadata — from `GET /api/views/{model}?type={form|list}`.

**Core principle:** The frontend renderer must be able to render any module's UI purely from the `arch_json` response, with zero module-specific code.

### Data flow

```
Module author writes view JSON file
        ↓
Startup sync loads it into ir_view
        ↓
GET /api/views/{model}?type=form
        ↓
Server resolves view + applies RBAC + annotates field metadata
        ↓
Frontend renderer walks components[] and renders by type + widget
        ↓
User interacts → frontend calls generic CRUD endpoints
```

---

## 2. Top-Level View Object

This is the full object returned by `GET /api/views/{model}?type={form|list}`.

```json
{
  "id": 12,
  "name": "employees.employee.form.default",
  "model": "ir_employee",
  "type": "form",
  "priority": 100,
  "arch_json": {
    "schema_version": 2,
    "title": "Employee",
    "actions": [],
    "components": []
  }
}
```

### `arch_json` root fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | integer | ✅ | Always `2`. Used by renderer to detect breaking changes. |
| `title` | string | ✅ | Human-readable page/section title. |
| `actions` | Action[] | ❌ | Buttons rendered in the form/list toolbar. Defaults to `[]`. |
| `components` | Component[] | ✅ | Ordered list of UI components to render. |
| `filters` | Filter[] | ❌ | Only valid on `type: list`. Defines the filter bar. |
| `columns` | Column[] | ❌ | Only valid on `type: list`. Defines visible table columns. |

---

## 3. View Types

| Type | Description | Key sections used |
|---|---|---|
| `form` | Single-record create/edit form | `actions`, `components` |
| `list` | Multi-record table with filters | `actions`, `columns`, `filters` |

---

## 4. Actions

Actions define the buttons rendered in the toolbar of a form or list view. They are always server-driven — the frontend never hardcodes Save or Delete.

```json
"actions": [
  {
    "name": "save",
    "label": "Save",
    "type": "submit",
    "style": "primary",
    "icon": "save"
  },
  {
    "name": "delete",
    "label": "Delete",
    "type": "delete",
    "style": "danger",
    "icon": "trash",
    "confirm": true,
    "confirm_message": "Are you sure you want to delete this record?"
  },
  {
    "name": "print_slip",
    "label": "Print Slip",
    "type": "rpc",
    "style": "secondary",
    "icon": "printer",
    "endpoint": "/api/ir_employee/{id}/print",
    "method": "POST"
  },
  {
    "name": "send_email",
    "label": "Send Welcome Email",
    "type": "rpc",
    "style": "secondary",
    "endpoint": "/api/ir_employee/{id}/send-welcome",
    "method": "POST",
    "confirm": true,
    "confirm_message": "Send welcome email to this employee?"
  }
]
```

### Action fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✅ | Unique identifier for this action. |
| `label` | string | ✅ | Button text shown to user. |
| `type` | enum | ✅ | See action types below. |
| `style` | enum | ❌ | `primary` \| `secondary` \| `danger` \| `ghost`. Default: `secondary`. |
| `icon` | string | ❌ | Icon name (platform-defined icon set). |
| `confirm` | boolean | ❌ | Show a confirmation dialog before executing. Default: `false`. |
| `confirm_message` | string | ❌ | Message shown in confirmation dialog. |
| `endpoint` | string | ❌ | Required for `rpc` type. URL template. `{id}` is replaced with current record id. |
| `method` | enum | ❌ | `GET` \| `POST` \| `PUT` \| `DELETE`. Default: `POST`. |
| `context` | object | ❌ | Extra key-value pairs merged into the RPC request body. |
| `permission` | string | ❌ | Permission code required to see this button. Server applies this — button is hidden if user lacks it. |

### Action types

| Type | Behaviour |
|---|---|
| `submit` | Serialises form state and calls `POST /api/{model}` (create) or `PUT /api/{model}/{id}` (edit). |
| `delete` | Calls `DELETE /api/{model}/{id}`. Should always have `confirm: true`. |
| `rpc` | Calls a custom `endpoint`. Renderer passes current record id and optional `context`. |
| `redirect` | Navigates to `endpoint` as a client-side route. No API call. |
| `wizard` | Opens a multi-step wizard modal. `endpoint` returns wizard `arch_json`. |

---

## 5. Components

All items in `components[]` share a common `type` discriminator field. The renderer switches on `type` to decide what to render.

### Common fields on all components

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | ✅ | Discriminator. See below. |
| `visible_if` | Condition | ❌ | Conditionally show/hide this component based on another field's value. |
| `colspan` | integer | ❌ | How many columns this component spans inside a `group`. Default: `1`. |

### Condition object (`visible_if`)

```json
"visible_if": {
  "field": "employment_type",
  "operator": "=",
  "value": "contract"
}
```

| Operator | Meaning |
|---|---|
| `=` | equals |
| `!=` | not equals |
| `in` | value is in list |
| `not_in` | value is not in list |
| `>`, `<`, `>=`, `<=` | numeric comparison |
| `set` | field has a non-null, non-empty value |
| `not_set` | field is null or empty |

---

### 5.1 `field`

Renders a labelled input widget for a model field.

```json
{
  "type": "field",
  "name": "employee_name",
  "label": "Employee Name",
  "widget": "char",
  "required": true,
  "readonly": false,
  "placeholder": "e.g. Ali Hassan",
  "help": "Full legal name as per CNIC",
  "colspan": 1
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✅ | Must match a column or relationship name on the model. |
| `label` | string | ✅ | Human-readable field label. |
| `widget` | string | ✅ | See Widget Catalogue (Section 6). Injected by server if omitted in file. |
| `required` | boolean | ❌ | Injected by server from field metadata. Can be overridden in view file. |
| `readonly` | boolean | ❌ | Injected by server from RBAC field rules. Can be forced `true` in view file. |
| `placeholder` | string | ❌ | Input placeholder text. |
| `help` | string | ❌ | Tooltip or helper text shown below the field. |
| `default` | any | ❌ | Default value pre-filled when creating a new record. |
| `visible_if` | Condition | ❌ | See Condition object above. |
| `colspan` | integer | ❌ | Column span inside parent `group`. |

---

### 5.2 `group`

A layout container that arranges its children in a responsive column grid.

```json
{
  "type": "group",
  "label": "Personal Information",
  "columns": 2,
  "children": [
    { "type": "field", "name": "employee_name", "label": "Name" },
    { "type": "field", "name": "employee_email", "label": "Email" }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | ❌ | Section heading. Omit for invisible layout grouping. |
| `columns` | integer | ❌ | Number of columns in the grid. Default: `2`. |
| `children` | Component[] | ✅ | Components to render inside this group. |
| `collapsible` | boolean | ❌ | Whether the group can be collapsed. Default: `false`. |
| `collapsed` | boolean | ❌ | Initial collapsed state. Default: `false`. |

---

### 5.3 `tabs` / `tab`

A tabbed container. `tabs` holds an array of `tab` components.

```json
{
  "type": "tabs",
  "children": [
    {
      "type": "tab",
      "label": "Work Info",
      "icon": "briefcase",
      "children": [
        { "type": "field", "name": "department_id", "label": "Department" },
        { "type": "field", "name": "job_title", "label": "Job Title" }
      ]
    },
    {
      "type": "tab",
      "label": "Leave History",
      "icon": "calendar",
      "children": [
        {
          "type": "field",
          "name": "leave_ids",
          "label": "Leaves",
          "widget": "one2many",
          "relation": "ir_leave",
          "inline_view": "leave.list.inline"
        }
      ]
    }
  ]
}
```

#### `tabs` fields

| Field | Type | Required | Description |
|---|---|---|---|
| `children` | tab[] | ✅ | Must only contain `type: tab` items. |

#### `tab` fields

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | ✅ | Tab heading text. |
| `icon` | string | ❌ | Icon displayed next to the label. |
| `children` | Component[] | ✅ | Components inside this tab. |
| `visible_if` | Condition | ❌ | Hide entire tab based on condition. |

---

### 5.4 `notebook`

A collapsible accordion section.

```json
{
  "type": "notebook",
  "label": "Emergency Contact",
  "collapsed": true,
  "children": [
    { "type": "field", "name": "emergency_contact_name", "label": "Contact Name" },
    { "type": "field", "name": "emergency_contact_phone", "label": "Phone" }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | ✅ | Section heading. |
| `collapsed` | boolean | ❌ | Initial state. Default: `false`. |
| `children` | Component[] | ✅ | Components inside. |

---

### 5.5 `separator`

A visual horizontal divider with an optional label.

```json
{
  "type": "separator",
  "label": "Contract Details"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | ❌ | Optional text displayed on or above the line. |

---

### 5.6 `html`

Renders a static HTML block. Use sparingly — only for banners, notices, or help text that cannot be expressed as a field.

```json
{
  "type": "html",
  "content": "<p class='notice'>This record is archived and cannot be edited.</p>"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `content` | string | ✅ | Raw HTML string. Renderer must sanitise before inserting into DOM. |
| `visible_if` | Condition | ❌ | Conditionally show the block. |

---

## 6. Widget Catalogue

The `widget` field on a `field` component tells the renderer which input control to use. If omitted in the view file, the server injects it from `IrField.field_type`.

---

### 6.1 `char`

Single-line text input.

```json
{ "type": "field", "name": "employee_name", "widget": "char", "max_length": 128 }
```

| Extra field | Type | Description |
|---|---|---|
| `max_length` | integer | Maximum character count. Injected from DB column length if available. |

---

### 6.2 `integer`

Integer number input.

```json
{ "type": "field", "name": "age", "widget": "integer", "min": 18, "max": 65 }
```

| Extra field | Type | Description |
|---|---|---|
| `min` | integer | Minimum allowed value. |
| `max` | integer | Maximum allowed value. |

---

### 6.3 `float`

Decimal number input.

```json
{ "type": "field", "name": "basic_salary", "widget": "float", "precision": 2 }
```

| Extra field | Type | Description |
|---|---|---|
| `precision` | integer | Decimal places to display. Default: `2`. |

---

### 6.4 `boolean`

Toggle switch or checkbox.

```json
{ "type": "field", "name": "is_active", "widget": "boolean", "style": "toggle" }
```

| Extra field | Type | Description |
|---|---|---|
| `style` | enum | `toggle` \| `checkbox`. Default: `toggle`. |

---

### 6.5 `date`

Date picker. Value format: `YYYY-MM-DD`.

```json
{ "type": "field", "name": "join_date", "widget": "date" }
```

---

### 6.6 `datetime`

Date + time picker. Value format: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`).

```json
{ "type": "field", "name": "last_login_at", "widget": "datetime" }
```

---

### 6.7 `text`

Multi-line textarea.

```json
{ "type": "field", "name": "notes", "widget": "text", "rows": 4 }
```

| Extra field | Type | Description |
|---|---|---|
| `rows` | integer | Initial visible rows. Default: `3`. |

---

### 6.8 `selection`

Dropdown with a fixed list of options. Options are **always defined in the view** (not fetched from an endpoint).

```json
{
  "type": "field",
  "name": "employment_type",
  "widget": "selection",
  "options": [
    { "value": "full_time", "label": "Full Time" },
    { "value": "part_time", "label": "Part Time" },
    { "value": "contract",  "label": "Contract"  }
  ]
}
```

| Extra field | Type | Description |
|---|---|---|
| `options` | Option[] | Required. Each option has `value` (stored) and `label` (displayed). |
| `allow_empty` | boolean | Whether a blank/null option is shown. Default: `true`. |

---

### 6.9 `many2one`

Searchable dropdown that fetches options from a related model.

```json
{
  "type": "field",
  "name": "department_id",
  "widget": "many2one",
  "relation": "ir_department",
  "display_field": "name",
  "search_fields": ["name", "code"],
  "domain": [["active", "=", true]]
}
```

| Extra field | Type | Description |
|---|---|---|
| `relation` | string | ✅ Target model name (table name). Injected by server. |
| `display_field` | string | Field on the related model to show as the label. Default: `name`. |
| `search_fields` | string[] | Fields to search on when user types. Default: `["name"]`. |
| `domain` | Filter[] | Pre-filter applied when fetching options. |
| `create_quick` | boolean | Allow creating a new related record inline. Default: `false`. |

**How the renderer fetches options:**
```
GET /api/{relation}?domain=<domain>&fields=id,{display_field}&page_size=20&search={query}
```

---

### 6.10 `one2many`

Inline editable table for child records (the "many" side of a one-to-many).

```json
{
  "type": "field",
  "name": "leave_ids",
  "widget": "one2many",
  "relation": "ir_leave",
  "inline_view": "leave.list.inline",
  "can_create": true,
  "can_delete": true
}
```

| Extra field | Type | Description |
|---|---|---|
| `relation` | string | ✅ Target model name. Injected by server. |
| `inline_view` | string | ✅ Name of a `list` type view to render inline. Renderer fetches it separately. |
| `can_create` | boolean | Show "Add a line" button. Default: `true`. |
| `can_delete` | boolean | Show delete row button. Default: `true`. |
| `domain` | Filter[] | Pre-filter on child records. |

---

### 6.11 `many2many`

Multi-select tag input backed by a related model.

```json
{
  "type": "field",
  "name": "skill_ids",
  "widget": "many2many",
  "relation": "ir_skill",
  "display_field": "name",
  "style": "tags"
}
```

| Extra field | Type | Description |
|---|---|---|
| `relation` | string | ✅ Target model name. Injected by server. |
| `display_field` | string | Field to display as tag label. Default: `name`. |
| `style` | enum | `tags` \| `checkboxes`. Default: `tags`. |

---

### 6.12 `file`

File upload field.

```json
{
  "type": "field",
  "name": "profile_photo",
  "widget": "file",
  "accept": "image/*",
  "max_size_mb": 2
}
```

| Extra field | Type | Description |
|---|---|---|
| `accept` | string | MIME type filter, e.g. `image/*`, `application/pdf`. |
| `max_size_mb` | integer | Maximum file size in megabytes. |
| `preview` | boolean | Show image preview after upload. Default: `false`. |

---

### 6.13 `monetary`

Currency-aware numeric input. Displays currency symbol.

```json
{
  "type": "field",
  "name": "salary",
  "widget": "monetary",
  "currency": "PKR",
  "precision": 2
}
```

| Extra field | Type | Description |
|---|---|---|
| `currency` | string | ISO 4217 currency code. Default: platform setting. |
| `precision` | integer | Decimal places. Default: `2`. |

---

### 6.14 `badge`

Read-only coloured label. Useful for status fields.

```json
{
  "type": "field",
  "name": "status",
  "widget": "badge",
  "readonly": true,
  "color_map": {
    "active":     "green",
    "on_leave":   "yellow",
    "terminated": "red"
  }
}
```

| Extra field | Type | Description |
|---|---|---|
| `color_map` | object | Maps field values to colour names. Colours: `green`, `yellow`, `red`, `blue`, `grey`. |

---

### 6.15 `progress`

Read-only progress bar. For numeric fields representing percentages.

```json
{
  "type": "field",
  "name": "profile_completion",
  "widget": "progress",
  "readonly": true,
  "max": 100
}
```

| Extra field | Type | Description |
|---|---|---|
| `max` | integer | Value that represents 100%. Default: `100`. |

---

## 7. Filter Bar (List Views)

Only valid on `type: list` views. Defines the filter controls shown above the table.

```json
"filters": [
  {
    "field": "employee_name",
    "label": "Search by Name",
    "operator": "ilike",
    "widget": "char"
  },
  {
    "field": "department_id",
    "label": "Department",
    "operator": "=",
    "widget": "many2one",
    "relation": "ir_department",
    "display_field": "name"
  },
  {
    "field": "is_active",
    "label": "Active Only",
    "operator": "=",
    "widget": "boolean",
    "default": true
  },
  {
    "field": "join_date",
    "label": "Joined After",
    "operator": ">=",
    "widget": "date"
  }
]
```

### Filter fields

| Field | Type | Required | Description |
|---|---|---|---|
| `field` | string | ✅ | Model field to filter on. |
| `label` | string | ✅ | Label shown on the filter control. |
| `operator` | string | ✅ | See operators below. |
| `widget` | string | ✅ | Same widget types as field components. Determines input type. |
| `default` | any | ❌ | Default filter value applied on page load. |
| `relation` | string | ❌ | Required if widget is `many2one` or `many2many`. |
| `display_field` | string | ❌ | Display field for relational filter widgets. |

### Filter operators

| Operator | Meaning |
|---|---|
| `=` | Exact match |
| `!=` | Not equal |
| `ilike` | Case-insensitive contains |
| `like` | Case-sensitive contains |
| `>`, `<`, `>=`, `<=` | Numeric / date comparison |
| `in` | Value in list |
| `not_in` | Value not in list |
| `is_null` | Field is null |
| `is_not_null` | Field is not null |

### How the renderer sends filters to the API

All active filters are serialised into a `domain` query parameter:

```
GET /api/ir_employee?domain=[["employee_name","ilike","ali"],["is_active","=",true]]&page=1&page_size=20
```

---

## 8. Server Enrichment

When the backend resolves a view via `GET /api/views/{model}?type={form|list}`, it **mutates the `arch_json` before returning it** by injecting metadata from `FieldCache` into each `field` node.

This means view JSON files on disk can be minimal:

```json
{ "type": "field", "name": "department_id", "label": "Department" }
```

And the server returns the full enriched version:

```json
{
  "type": "field",
  "name": "department_id",
  "label": "Department",
  "widget": "many2one",
  "required": false,
  "readonly": false,
  "relation": "ir_department",
  "display_field": "name"
}
```

### Enrichment rules (server-side)

| Injected field | Source | Override allowed in view file? |
|---|---|---|
| `widget` | `IrField.field_type` mapped to widget name | ✅ Yes |
| `required` | `IrField.required` | ✅ Yes (view can make optional fields required, not vice versa) |
| `readonly` | RBAC `FieldAccess.can_write` | ❌ No — RBAC always wins |
| `relation` | `IrField.relation` | ❌ No |
| `max_length` | DB column length | ✅ Yes |

### `field_type` → `widget` mapping (server default)

| `IrField.field_type` | Default widget |
|---|---|
| `VARCHAR` / `String` | `char` |
| `INTEGER` | `integer` |
| `FLOAT` / `NUMERIC` | `float` |
| `BOOLEAN` | `boolean` |
| `DATE` | `date` |
| `DATETIME` | `datetime` |
| `TEXT` | `text` |
| `many2one` | `many2one` |
| `one2many` | `one2many` |
| `many2many` | `many2many` |

---

## 9. Field-Level Access Rules

RBAC rules are applied **server-side** before the view is returned. The frontend never makes access decisions.

| Scenario | Result |
|---|---|
| User cannot read field | Field node is **removed** from `components[]` entirely |
| User can read but not write | Field node is returned with `"readonly": true` injected |
| User can read and write | Field node returned as-is |
| Super admin | All fields returned, no restrictions |

This means a renderer that simply renders all `components[]` is automatically RBAC-compliant.

---

## 10. Complete Examples

### 10.1 Employee Form View

**File:** `modules/employees/views/employee_form.json`

```json
{
  "name": "employees.employee.form.default",
  "model": "ir_employee",
  "type": "form",
  "priority": 100,
  "active": true,
  "groups": [],
  "arch_json": {
    "schema_version": 2,
    "title": "Employee",
    "actions": [
      {
        "name": "save",
        "label": "Save",
        "type": "submit",
        "style": "primary",
        "icon": "save"
      },
      {
        "name": "delete",
        "label": "Delete",
        "type": "delete",
        "style": "danger",
        "icon": "trash",
        "confirm": true,
        "confirm_message": "Permanently delete this employee?"
      }
    ],
    "components": [
      {
        "type": "group",
        "label": "Personal Information",
        "columns": 2,
        "children": [
          {
            "type": "field",
            "name": "employee_name",
            "label": "Full Name",
            "required": true
          },
          {
            "type": "field",
            "name": "employee_email",
            "label": "Work Email",
            "required": true
          },
          {
            "type": "field",
            "name": "department_id",
            "label": "Department"
          },
          {
            "type": "field",
            "name": "employment_type",
            "label": "Employment Type",
            "widget": "selection",
            "options": [
              { "value": "full_time", "label": "Full Time" },
              { "value": "part_time", "label": "Part Time" },
              { "value": "contract",  "label": "Contract"  }
            ]
          }
        ]
      },
      {
        "type": "group",
        "label": "Status",
        "columns": 2,
        "children": [
          {
            "type": "field",
            "name": "join_date",
            "label": "Joining Date"
          },
          {
            "type": "field",
            "name": "status",
            "label": "Status",
            "widget": "badge",
            "readonly": true,
            "color_map": {
              "active":     "green",
              "on_leave":   "yellow",
              "terminated": "red"
            }
          }
        ]
      },
      {
        "type": "tabs",
        "children": [
          {
            "type": "tab",
            "label": "Leave History",
            "children": [
              {
                "type": "field",
                "name": "leave_ids",
                "label": "Leaves",
                "widget": "one2many",
                "relation": "ir_leave",
                "inline_view": "leave.list.inline",
                "can_create": true,
                "can_delete": false
              }
            ]
          },
          {
            "type": "tab",
            "label": "Skills",
            "children": [
              {
                "type": "field",
                "name": "skill_ids",
                "label": "Skills",
                "widget": "many2many",
                "relation": "ir_skill",
                "display_field": "name",
                "style": "tags"
              }
            ]
          }
        ]
      },
      {
        "type": "notebook",
        "label": "Emergency Contact",
        "collapsed": true,
        "children": [
          {
            "type": "group",
            "columns": 2,
            "children": [
              {
                "type": "field",
                "name": "emergency_contact_name",
                "label": "Contact Name"
              },
              {
                "type": "field",
                "name": "emergency_contact_phone",
                "label": "Phone Number"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

### 10.2 Employee List View

**File:** `modules/employees/views/employee_list.json`

```json
{
  "name": "employees.employee.list.default",
  "model": "ir_employee",
  "type": "list",
  "priority": 100,
  "active": true,
  "groups": [],
  "arch_json": {
    "schema_version": 2,
    "title": "Employees",
    "actions": [
      {
        "name": "create",
        "label": "New Employee",
        "type": "redirect",
        "style": "primary",
        "icon": "plus",
        "endpoint": "/employees/new"
      }
    ],
    "columns": [
      {
        "field": "employee_name",
        "label": "Name",
        "sortable": true
      },
      {
        "field": "employee_email",
        "label": "Email",
        "sortable": false
      },
      {
        "field": "department_id",
        "label": "Department",
        "sortable": true,
        "widget": "many2one",
        "display_field": "name"
      },
      {
        "field": "status",
        "label": "Status",
        "widget": "badge",
        "color_map": {
          "active":     "green",
          "on_leave":   "yellow",
          "terminated": "red"
        }
      }
    ],
    "filters": [
      {
        "field": "employee_name",
        "label": "Search by Name",
        "operator": "ilike",
        "widget": "char"
      },
      {
        "field": "department_id",
        "label": "Department",
        "operator": "=",
        "widget": "many2one",
        "relation": "ir_department",
        "display_field": "name"
      },
      {
        "field": "status",
        "label": "Status",
        "operator": "=",
        "widget": "selection",
        "options": [
          { "value": "active",     "label": "Active"     },
          { "value": "on_leave",   "label": "On Leave"   },
          { "value": "terminated", "label": "Terminated" }
        ]
      }
    ]
  }
}
```

---

## 11. Validation Rules

These rules are enforced by the backend when syncing view files at startup.

| Rule | Error |
|---|---|
| `schema_version` must be present and equal to `2` | `Invalid schema_version` |
| `title` must be a non-empty string | `title is required` |
| Every `field` node must have `name` and `label` | `field missing name or label` |
| `selection` widget must have non-empty `options[]` | `selection widget requires options` |
| `many2one` widget must have `relation` (or it is injected from field cache) | `many2one missing relation` |
| `one2many` widget must have `relation` and `inline_view` | `one2many missing relation or inline_view` |
| `actions[].type` must be a known type | `unknown action type` |
| `rpc` action must have `endpoint` | `rpc action missing endpoint` |
| `columns[]` only valid on `type: list` | `columns not allowed on form view` |
| `filters[]` only valid on `type: list` | `filters not allowed on form view` |

---

## 12. Versioning

| `schema_version` | Status | Notes |
|---|---|---|
| `1` | Deprecated | Original flat components list, no actions, no filters. Still loaded but renderer shows warning. |
| `2` | Current | Full spec as described in this document. |

When a breaking change is required in future, increment to `3` and support a migration path in the server enrichment layer.

---

## 13. Frontend Renderer Contract

The renderer must follow these rules to remain module-agnostic:

1. **Never hardcode model names.** All model info comes from the view response.
2. **Never hardcode field names.** Walk `components[]` dynamically.
3. **Never hardcode Save/Delete buttons.** Render `actions[]` generically.
4. **Trust `readonly` from the server.** Never compute access rules on the frontend.
5. **Trust `widget` from the server.** Map `widget` → React component using a registry.
6. **For `many2one` / `many2many` options**, call `GET /api/{relation}?search={query}` — never hardcode options.
7. **For `one2many` inline tables**, fetch the `inline_view` separately via `GET /api/views/{relation}?type=list&name={inline_view}`.
8. **Serialise form state as a flat JSON object** keyed by field `name`. Send to `POST /api/{model}` or `PUT /api/{model}/{id}`.
9. **Unknown `type` or `widget` values** must render a fallback placeholder, never crash.
10. **Unknown fields** in `arch_json` must be silently ignored for forward compatibility.

### Widget registry (frontend pseudocode)

```javascript
const WIDGET_MAP = {
  char:      CharInput,
  integer:   IntegerInput,
  float:     FloatInput,
  boolean:   BooleanToggle,
  date:      DatePicker,
  datetime:  DateTimePicker,
  text:      Textarea,
  selection: SelectDropdown,
  many2one:  Many2OneSearch,
  one2many:  One2ManyTable,
  many2many: Many2ManyTags,
  file:      FileUpload,
  monetary:  MonetaryInput,
  badge:     BadgeDisplay,
  progress:  ProgressBar,
};

function renderField(node) {
  const Widget = WIDGET_MAP[node.widget] ?? UnknownWidgetFallback;
  return <Widget field={node} />;
}
```

---

*This document is the single source of truth for the `arch_json` schema. Any change to this spec must be reflected in the backend enrichment logic, the startup validator, and the frontend widget registry simultaneously.*
