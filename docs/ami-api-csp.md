## Sending job applications to PE internal service AMI (API CSP)

AMI stands for `Acte métier d'intermédiation`. It is an internal service of Pôle emploi aiming at centralizing information about actions made by job seekers to attempt to find a job.

It makes sense that LaBonneBoite and JePostule send information about each job application to this service.

Sending this information about each job application is made from JePostule by calling an internal AMI API called `API Candidature Spontanée`, `API CSP` for short.

The way the `API CSP` expects us to identify the applicant is tricky. It requires a valid PEAMU access token which, as PE Connect is only implemented on LBB and not JP, has to come from LBB. 

Historically the PEAMU access token of a given user was only valid for a few minutes after the user initially connects via PE Connect. Then the user would stay connected on LBB forever despite having an expired PEAMU access token. This was simpler for our user experience (no need to reconnect ever).

However the AMI requirements changed this. Suddenly we have to have a valid PEAMU access token at all times to forward it to JP so that JP can authenticate the user with it when calling the API CSP.

Thus we now refresh the PEAMU access token frequently, though no more than once every two hours per user, each time the user visits the home, search result page or job application page.

Note that in theory, the PEAMU access token is supposed to be valid for up to six months. Which means that in theory, the only case where a user would be disconnected is if they did not visit LBB for six months or more. Whether or not this theory stays true in practice depends on ESD to actually stand by their claim that the PEAMU access token stays valid for six months, we have no direct way to independently ensure this.

For security reasons, the PEAMU access token is encrypted when forwarded from LBB to JP, so that the user never has access to it directly.

For more information about implementation on JP side, there is some additional documentation in the [official JP README](https://github.com/StartupsPoleEmploi/jepostule).

