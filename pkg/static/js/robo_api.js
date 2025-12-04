/**
 * Robot client API functions.
 */

async function api_send_direction(direction, x, y)
{
    stop_sync = true;
    console.log("api_send_direction()")

    direction= {
        "direction": direction,
        "x": x,
        "y": y,
    };

    console.log(direction);
    $.ajax("/api/motion/direction",
    {
        type : 'POST',
        data : JSON.stringify(direction),
        contentType : 'application/json',
        success: function(response)
        {
            console.log("Success:", response);
        },
        error: function(xhr, status, error)
        {
            console.error("Error:", status, error);
        }
    });
}


async function api_send_ptz(pan, tilt, zoom)
{
    stop_sync = true;
    console.log("api_send_ptz()")

    ptz_record = {
        "pan": pan,
        "tilt": tilt,
        "zoom": zoom
    };

    console.log(ptz_record);
    $.ajax("/api/camera/ptz",
    {
        type : 'POST',
        data : JSON.stringify(ptz_record),
        contentType : 'application/json',
        success: function(response)
        {
            console.log("Success:", response);
        },
        error: function(xhr, status, error)
        {
            console.error("Error:", status, error, ptz_record);
        }
    });
}


async function api_send_focus(auto_focus, focus_value)
{
    stop_sync = true;
    console.log("api_send_focus()")

    focus = {
        "auto": auto_focus,
        "value": focus_value
    };

    console.log(focus);
    $.ajax("/api/camera/focus",
    {
        type: 'POST',
        data: JSON.stringify(focus),
        contentType: 'application/json',
        success: function(response)
        {
            console.log("Success:", response);
        },
        error: function(xhr, status, error)
        {
            console.error("Error:", status, error);
        }
    });
}


async function api_get_ptz()
{
    return JSON.parse(await $.getJSON("/api/camera/ptz"));
}


async function api_get_zoom()
{
    return (await api_get_ptz())["zoom"];
}


async function api_get_focus()
{
    return JSON.parse(await $.getJSON("/api/camera/focus"));
}


async function api_get_controls()
{
    return $.getJSON("/api/camera/controls");
}


async function api_reset()
{
    console.log("api_reset()");
    return $.ajax("/api/camera/reset",
    {
        type : 'POST',
        contentType : 'application/json',
        success: function(response)
        {
            console.log("Success:", response);
        },
        error: function(xhr, status, error)
        {
            console.error("Error:", status, error);
        }
    });
}
