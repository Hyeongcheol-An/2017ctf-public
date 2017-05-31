# Notice for Notary service 

Here we provide the setting for 'pubkeys/'. Below is the setting for team 1. 
Note that we didn't include the public keys of all the team members,

```
# Snippet from Dockerfile 
ADD ./is521-ta.pub /home/notary/notary/pubkeys/ta.pub
ADD ./Team1-Client.pub /home/notary/notary/pubkeys/team1.pub
```
