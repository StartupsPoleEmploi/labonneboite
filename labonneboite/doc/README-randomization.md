# About the randomization aka weighted shuffling of our results.

Historically by default we would sort our results for a given ROME code and a given geolocation by (descending) score and thus show on the first page of results the companies having the top 20 scores.

The problem with this approach is that most people will focus on the first page only of results resulting in too many applications on the top 20 companies and not enough on the companies of the remaining pages.

LBB's goal is to promote applications not only to the top 20 companies for each search but also to all companies which we predict they are hiring, depending on "how much" we think they are hiring.

This is why we decided to shuffle all our results and weight this shuffling by company scores. A company having score 100/100 will have 5 times as many chances to be on the first page of results than a company having score 20/100. But this way smaller companies will have their chance too.

This weighted shuffling is reset every 24 hours at midnight.

We name this weighted shuffling `Tri optimisé` on the frontend.

The fact that the company results are not sorted by score might be confusing to the frontend user, this is why we added a `Tri exclusif LaBonneBoite basé sur le potentiel d'embauche des entreprises mis à jour toutes les 24 heures` tooltip to help lessen the confusion.

## Technical documentation

This randomization is implemented in the elastic search request with a random seed based on the current date, thus automatically refreshed every midnight. See the `# 2) overload main_query to add smart randomization` section in [common/search.py](https://github.com/StartupsPoleEmploi/labonneboite/blob/master/labonneboite/common/search.py#L607).