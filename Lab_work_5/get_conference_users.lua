local frandom = io.open("/dev/urandom", "rb")
local d = frandom:read(4)
math.randomseed(d:byte(1) + (d:byte(2) * 256) + (d:byte(3) * 65536) + (d:byte(4) * 4294967296))

number = math.random(1, 2)
request = function()
    headers = {}
    headers["Content-Type"] = "application/json"
    return wrk.format("GET", "/conference_users/"..tostring(number), headers)
end