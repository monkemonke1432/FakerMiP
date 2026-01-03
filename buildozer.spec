[app]
title = FakerMiP
package.name = fakermip
package.domain = org.monke
source.dir = .
version = 0.1

# 1. INCLUDE YOUR ASSETS
# Add wav and png to the list of extensions to bundle
source.include_exts = py,png,wav

# 2. REQUIREMENTS
# Note: pyjnius is needed for the Multicast Lock
requirements = python3==3.11.9,pygame-ce,pyjnius

# 3. PERMISSIONS
# These are the "Big Four" for MiP connectivity
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CHANGE_WIFI_MULTICAST_STATE, ACCESS_WIFI_STATE

# 4. PREVENT SCREEN SLEEP (Optional but recommended)
# This keeps MiP on screen while dancing
android.wakelock = True

# there used to be a package tip thing here but we dont need that since everything is on root