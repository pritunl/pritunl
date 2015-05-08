# pritunl: single sign on filters

The files in this directory can be used to modify the behavior of the single
sign on filters. Currently only the google filter is available which will
receive a valid gmail or google apps email address as input. Any email
including gmail.com addresses and ones that do not match your google apps
domain could potentially be used as input. The filter should expect email
addresses to be inputted multiple times as each time a user uses the single
sign on it will re-verify the user. If the user has already signed in before
their user will be queried and the same key will be given to them. The default
filter will allow only google apps email addresses from the domains set in the
single sign on settings. In addition to the users email address the default
organization id is included this is the organization that is selected in the
single sign on settings. By default the same organization id is returned which
will add the user to that organization. This can be changed by returning a
different organization id to customize which organization the users will be
added to. Organization ids can be retrieved using the code in the org
directory or by going into the web interface and holding shift then click the
green "Organization" label. This will display all the object ids for that
organization. Organization ids never change including when an organization is
renamed. Filter modifications only need to be made on the forward facing
instances that the users will go to when signing in. Other instances in the
cluster will not need to be modified if the instances are not used for single
sign on.
