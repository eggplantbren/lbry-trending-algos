Desiderata for a Trending Algorithm
===================================

An ideal trending algorithm would have the following properties.
All of the ones that exist meet at least a few of these criteria, but none
satisfies all of them. It could be impossible to satisfy all of them.

## Which quantities should be used (more)

  * It should mostly use on-chain quantities, to reduce/remove reliance on
    authorities such as LBRY, Inc.

## LBC

  * An increase in the total amount on a claim (bid + support_amount)
     should improve its trending performance
  * A decrease in the total amount should hurt a claim's trending performance
  * It should be possible for a user with a lot of LBC to use it to make
    a claim trend artificially.
  * On the other hand, it should *not* be possible for
    a single user or a small group of users to dominate trending
    _for a large proportion of the time_ (Tom's time-locked supports and/or
    my delayed_ar version mitigate this).
  * A claim that receives a small amount of LBC spread over many supports
    should have a chance against claims with a lot of LBC.
  * However, it should be difficult or impossible,
    to use the previous point and a script to dominate trending
    for a large proportion of the time (i.e., perhaps it is possible to do
    this but then you have to wait before you can do it again). 

## Time

  * Recent changes should have a greater effect than changes that happened
    further in the past
  * Ideally, trending scores/ranks should be updated quite frequently, so
    the experience is responsive

## Reposts

  * Other on-chain quantities such as reposts could, and probably should,
    be used, though there
  * If so, it should not be possible to artificially make a claim trend
    by reposting it from worthless dummy channels created for this purpose.

## Trending list

  * The top trending spots should include a mix of things that are trending
    in an absolute sense (i.e., more popular than everything else recently)
    and things that are trending in a relative sense (i.e., more popular than
    it used to be).

  * However, it should not include things that are trending in a relative
    sense but performing poorly in an absolute sense (e.g., something that
    had 0 views, then suddenly jumped to 5, should not be high in trending).

  * In my opinion, the top 20 or so trending spots should be about a 75/25
    mixture of organically popular content and promoted content, respectively.

