Introduction
0:01
Hi everyone, welcome to this video. So this video is going to be how to adapt to regime changes.
0:08
And so the goal of this video really is to show like how you can adapt your strategy to when there's huge changes in
0:14
the distribution of your your data which we call like a regime change. So for example, taking like a a strategy that's
0:23
not adaptive that might look like something like this to make it more uh adaptive. So the it it looks a much
0:32
better equity curve. And there's that's actually more than four ways, but we're going to look at
0:37
four different methods to to handle uh regime shifts and to make our trading
0:44
more adaptive. Uh but before we go into we need to define what actually is a
What is a Regime Change?
0:50
regime change. So we need some sort of like mathematical definition. And uh so to summarize in one sentence
0:57
we can say that it can be modeled as when the time series exhibits non-stationary dynamics. Uh so we need
Stationarity vs Non-Stationarity
1:05
to understand what is stationerity. Uh so stationerity is when the statistical properties are invariant
1:11
over time. So this means that they stay constant uh over time. Uh and the
1:17
properties more specifically are the mean which is the a measure of central location. So that's the the the highest
1:25
point essentially in in a distribution uh and the the variance which is a
1:32
measure of the spread of the distributions. Maybe if I show you like a distribution here. Okay. So this is
1:38
the returns distribution for Bitcoin dollar. So the the central location is like the uh the peak of the distribution
1:47
like the central location and then the spread is like the the width of the distribution essentially
1:55
and then we've got the the third moment is the skewess which measures like how
2:01
symmetric it is. So if it's not symmetric then it's skewed on one side.
2:06
Uh so that's one important measure and then the other one uh another important measure is the
2:13
ketosis which essentially is a measure of uh your fat tails. How these are the
2:19
tails right which is like extreme events and uh the higher the ktosis the more
2:26
chance of like a very extreme event happening. So these are the four moments of of a
2:32
distribution which is and the stationary assumes that they're constant and essentially invariant over time. Uh but
2:41
we're going to show you that uh in practice this is never there they're there are never stationary time series.
2:47
Uh I think in practice there's only like for example uh there's very few that are
2:55
stationary. For example, you could have like a a very high sharp trading strategy and you look at the the P&L of
3:02
it that will probably be stationary because it's like a pretty much like a straight line.
3:08
But uh let's have a look at uh yeah so anyway here's here's the for example
3:13
just looking at the the moments of the distribution we can see like uh a concrete example where the mean is
3:20
positive so on average it goes up. uh standard deviation a measure of the the
3:26
variance of 3%. Uh and then the skewed this means it's posit positively skewed
3:32
[snorts] and then a ktosis of like three. So the uh those tails here fat tails so the
3:41
likely the higher the ktosis the higher the chance of extreme price movements.
3:46
[snorts] And the key question here is like are BTC returns stationary? uh
3:52
there are lots of like stat uh tests statistical tests that we could do but I think we can just look empirically and
3:58
just see like uh so what I've done is grouped the the returns by the moments
4:04
uh by year aggregating the the statistical moments and you can see here
4:10
like for example in 20 like the pretty much positive apart from a negative mean
4:16
in 2022 and in 2026 and you can see for example in 2026
4:23
the there's more extreme price movements uh in 2026 let's say compared to I don't
4:28
know 2021 and we look at like the symmetry we can see like there's a negative symmetry
4:35
here for when um 2022 and I think this is direct pertaining to when I think uh
4:42
FTX collapsed right so this like just crashed uh BTC
4:48
okay So, so you should see here and even just by looking at the chart you can sort, you
4:54
know, you don't have to be a rocket scientist to to see here that uh
5:00
there's like trends here uh and you know huge fluctuations in prices. So for
5:08
example here in 2022 it like shoots down right but then in uh 202425
5:15
it just like shoots up. Uh so there's huge structural changes in the
5:20
distribution of the returns and so the key question is is like how do you handle this like non-stationerity
5:26
behavior especially like in supervised learning which is the most common form of like machine learning.
5:33
So let's say we we got a model to predict future returns and we're just going to use the the current return.
5:40
This is what's called like an auto reggressive model. uh in econometrics this is called uh an AR1 model and so
5:50
we're essentially saying is that the future R which is log return is that the
5:55
future log return is basic equals a weight which we we will determine by
Train Non Adaptive Model
6:00
machine learning uh the weight multiplied by the the current log return
6:06
plus a bias so before we do that we need to add to calculate the log returns
6:11
which we do now okay and I've created a function here that trains a linear regression model. Uh so we split the
6:19
data into train and test. Uh what's really important here is that we don't shuffle the data. So we what we call
6:25
preserve temporal order which is the order of the time. So we never like leak any future data points it does not know
6:32
about in the in the train. Uh so we've done that and then we fit the data with
6:39
the training data. So we don't fit it with all the data because we need to preserve some data uh to for a back
6:45
test. But we're going to do for the back test is test against all the the in sample and the outer sample data uh just
6:52
to show because it's also important that we have good insample statistics as well. And so I've just got this model
6:59
and so what I've done is I've uh run the model just against the previous uh
7:05
return to predict the future return. Okay. And you can see this is the equity
7:11
equity curve. But there's nothing wrong with this. Uh
7:16
so this is the what's the weight? So this is a mean reversion model because it has a negative uh waiting and then
7:23
there's a positive bias as well. Uh so the but the problem is if I go down is
7:31
that it looks identical to the actual time series itself. It's just but in a different scale. So this automatically
7:38
like is a red flag and when we look at the the distribution of the signal which is basically uh maybe if I show you the
7:44
signal it's basically the the sign of the prediction yhat being our the the
7:50
model's prediction and we convert into the our signal is uh and then we
7:56
obviously calculate the what the the trade would be. If we look at the distribution, it's just like 98% of the
8:04
time it's predicting uh to go up. So
8:09
this is why it looks equivalent to the actual underlying time series because it's just going up all the time. So this
8:17
is not really adaptive and you can see it's not adaptive because when we we saw in like in 2022 to uh 23 is that uh you
8:26
know it goes down on average and you can see here that it also goes down. So uh it's not adaptive to these regime
8:32
changes. So what can we do about it? And I mentioned that one of the one of the
Sliding Window
8:38
things we can do is this sliding window approach. Uh I'm personally not a big
8:44
fan of it uh because essentially you're just looking for a local pattern localized pattern to predict the next uh
8:52
time slice and it's also very sensitive to how big your window sizes and uh so
8:58
uh I've just shown like an example here. So it's like okay we split it into let's say like n windows we predict we train
9:05
on the first I don't know k windows to predict the next uh m windows. So you
9:14
can see like for example here like okay we're using the the first four windows
9:19
to predict the the fifth window and then we just shift it across um predict okay but this uh but we're not using all the
9:26
data to to predict and uh you know this could possibly work but I'm just not a
9:33
personal fan I just feel it's like a a t- version of like uh because you're just taking a subset of of the data
Encoding Hidden States
9:41
Right. [snorts] Uh so another form is that we can encode
9:46
memory. And so essentially what you can do do is like take this like uh several
9:52
data points like because financial time series data is extremely noisy and we
9:57
can compress it into a fing single file. Uh we can take a vector of past returns
10:03
and compress it into a single scaler. And this is essentially like a form of
10:08
like a hidden state. Uh and the idea is that uh we can encode like the memory uh
10:15
the the uh the current dynamics of the the returns and this is what we do here.
10:22
Uh it's really important that we're doing this rolling statistics. So this is basically just looking at the
10:27
previous 40 returns and taking the average. [snorts] And what's really important though is
10:34
that I'm doing it on not on closed log return but the lag because otherwise we would have data leakage because it would
10:40
be encoding the a future return it would not know about and so there'd be data
10:46
leakage there. Uh so that's a very important note.
10:52
And so we're just like summarize we're adding up and then we're taking the mean and then so we're going to do exactly
10:58
the same uh model uh autogressive model but instead of just passing in the the
11:05
lag warm we're going to take the the moving average of it. And you can see here automatically that uh uh it looks
11:13
much better now. So uh when there was like this huge price drop uh from 2022
11:19
to 20 [snorts] 22 to 23 uh we don't see this huge drop in the the draw down
11:25
right and for example here in you know just the beginning of 2026 there's a big
11:31
change right uh so but let's have a look at the distribution of the data you can see here that it was roughly about 100
11:38
you know data point like times it went predict down right and you can see here that it's actually increased so it is
11:44
adaptive right so if it if um ah and we should have a look and we see what the model is so this is a a momentum type of
11:51
model right and this is the beauty of like linear regression algorithms because I can just easily interpret it
11:56
if this is a neon network I would have no clue like why did it decide to go up or down but uh this is like a because
12:04
it's just a you know there's just two parameters I can really interpret like the the dynamics [snorts] and you can
12:13
see here that it's increased the number of data points that it's uh uh predicted down. So it's more adaptive when there
12:20
is actually like a regime change like for example in 2022. Okay. So now we looked at uh encoding
12:27
memory but what about modeling relative memory? So for example we could pass in
12:32
the the the moving average but we can also pass in the the current log return.
12:39
And we look at the models here. It's taking the model is essentially taking the difference between uh a weighted
12:46
difference of the the current log return against and you know against a weighted
12:55
uh value of the the moving average. [snorts] Uh and you can see here that there's
13:02
obviously a bigger weight here for for the the moving average. And you can see here that it's even more you know it
13:09
looks completely different from the the actual underlying. So from our original
13:14
model that we did the linear model with just the lag one which is pretty much you know going upward the whole time you
13:20
can see here uh it looks completely different right it's more adaptive. So when there's a huge structural change a
13:27
regime change like for example here you can see that it still makes money. And if we looked at the like the winning
13:32
rate, it will probably only be about like 51% 50.5%.
13:37
It won't be like a huge winning rate. Uh but you can just see here that uh it's more adaptive, right? And this is uh
13:45
essentially just a form of feature engineering for our supervised learning. And again, if we look at the the
13:50
distribution of the the signals, you can see that it's uh it's increased the
13:56
number of times it's predicted down. So that previously it was about 300 and now this is like over 400. So you can see by
14:04
making it more adaptive to you know to bet down that uh when it actually does go down that uh we make money here.
14:13
So that's in a in a s that's covering how to essentially do feature engineering uh to make your
Online Learning
14:21
create features that are more adaptive to non-stationity. Right. uh but now we're going to look at uh a different
14:28
form of learning algorithms which are called online learning and and
14:33
essentially we're going to look at what's called uh this passive aggressive regressor. So it's what it's going to do
14:39
is it's going to to continually change the weights of our linear regression. So
14:45
for example, it could like in one date time step it could be saying okay this is a a momentum type of strategy a
14:53
positive coefficient and suddenly maybe in a few data points it it changes to be
14:58
a mean reversion so it has a negative uh a negative weight [snorts] and the idea
15:04
is is that uh how it how does it change the weight so it does it uses this what's called a passive aggressive
15:10
learning uh and essentially what happens is if it if it predicts correctly
15:15
uh it doesn't change the weight. Okay. But then if it uh if if the model if the
15:20
predictions too deviates away too much then it uh corrects it. So this is a
15:26
form of like error correction and it's proportional to the to the amount of error in the prediction. Uh so for
15:34
example here and what's very important is that for example just all the the the
15:39
learning that we've been doing our machine learning has just been all passed all the data at once it's like a
15:45
full batch and then we it's oh and that's another important thing is that this is uh the learning regression if I
15:52
go up is a closed form solution so you you pass all the data in it's a closed
15:59
form solution uh ordinarily squares and then altogether what minimizes the the
16:05
error. Okay. Uh but with this let me just go back to here. This is more or
16:11
this online learning is more of a streaming. We don't pass all the data at once. So uh and this like complements uh
16:19
non-stationerity in financial time series because we just get a new data point. We pass it in make a prediction.
16:25
If the prediction's wrong, we make a an adjustment to the weights. And then
16:30
these are what's called like hyperparameters. I won't go into what all these hyperparameters are, but
16:36
again, we're just going to use the the previous uh the current return to predict the future log return. Uh we've
16:43
got this thing here like a standard scaler which is to scale it for the because we ah I point this out. So this
16:50
is what's called a stochastic gradient descent. uh this is like the most common uh machine learning algorithm the to to
16:58
do the learning. So we've got a machine learning algum to to adjust our weights do like error
17:04
correction. Uh so I think the most important thing here is that you know
17:09
the train step it's not it's a partial fit. So we just pass in one data point at a time make the fit it. So basically
17:18
run the stocastic gradient descent work out what the the weight and the bias is
17:23
at each time step because we're going to record it and display in a pandanda's data frame. Then we also take the the
17:29
predicted value and we take the the sign of it. That's our signal and again we just calculate what the the trade return
17:37
would be uh the log return more specifically and uh and then we just put
17:43
it into this records was uh because we're going to store in a pandas data frame and here out of the loop we then
17:50
create our data frame the results uh and then we just take the cumulative trade log return to to display our gross
17:57
equity curve and and we're also just going to calculate the the the directional hit rate right uh without
18:04
any form of like hyper optimization of the parameters right so we can just look and see what's happening here so it's
18:10
one like 50 just o over 50% of the the time and you can see uh if it's one or
18:18
not and you can see what's very important here is that for example in the the second tick it it pred the the
18:25
weight is a momentum uh style model right but in the next tick it's a mean
18:31
reversion uh bottle [cough and snorts] poor, pardon me. And uh yeah,
18:40
this is and you can see it's changing, right? It stays momentum, but then suddenly it changes to mean reversion,
18:46
right? And this is the again the beauty of of doing this on a linear regression because you know there's just two
18:52
parameters here to do the the learning. So we don't have this thing what's called the cursive dimensionality. we have like so many parameters that uh it
18:59
becomes like a an MP hard problem. Uh so okay so that's the and you can see the
19:06
the weights are are adaptive right and in our supervised that that weight is
19:11
constant and it's invariant over time right and you can see here that it's adaptive and we can actually you we can
19:21
oh maybe I just showed the equity curve and we look at the distribution here it's actually nearly 50/50 going up and
19:27
50 going down right [snorts] so uh and we Look at the equity curve.
19:33
uh it's not it doesn't the returns we need to would have to calculate the the
19:38
sharp of this right but uh it looks a lot a lot more smoother right uh
19:43
obviously the returns aren't great as the supervised but we haven't done any form of like hyp hyperparameter
19:50
optimization which is these uh the models parameters we haven't optimized
19:55
any of these to to improve this right so I've just uh picked this and again this
Reinforcement Learning
20:00
is this passive aggressive learning Right. And then we have a look at the underlying time series. You can see here
20:06
when it was like shooting down, it actually makes money when it was shooting down. And let's have another
20:11
example. So when it was like trending upwards that also uh made money here as
20:18
well. So you can see that it's made money both when it's trended down downwards and it's when it's open
20:26
when it's trended trending upwards. But we can make this even more uh
20:32
adaptive by just choosing some good hyper parameters to to this. Okay. So
20:38
that's online learning. Uh so now let's look into reinforcement learning. Uh so
20:44
I'm going the next video I'm going to do is going to be uh a video on reinforcement learning. So it's a whole
20:51
video dedicated to itself because we this video would be like 2 hours long if
20:56
we just if I went into the into the depth of uh reinforcement learning. [snorts] So reinforcement learning is
21:02
quite similar to the online learning where it's like if there's good behavior or good tradings we give it a reward but
21:09
if it's bad trades we we penalize it. So the idea is is that it cont it makes
21:16
good trades uh and we can formulate trading as uh so oh that's a good point.
21:23
So okay so with this um reinforcement learning I just want you to imagine that
21:28
you know we we're at a casino we've got a Hawaii Hawaiian shirt on uh sipping
21:34
cocktails and we we're we've gone to a bandit. So this is like a a bandit, but
21:40
we're going to go to like a two armed bandit. And essentially trading you can you can model it as a as a two armed
21:48
bandit problem. Okay, which is we don't know the we pull on one uh essentially
21:55
let's say the right arm is to predict going up and the left arm is to predict going down right and this is uh and we
22:01
don't know what the underlying distribution of the data is right uh and it's partially observable. We only we we
22:08
don't know what the true distribution o of the of the of the rewards, right? So
22:13
we need to play the game or play on this bandit to understand the true distribution and obviously it could also
22:21
the distribution could completely change. It could be non-stationary, right? So we're just to just to gently
22:28
break you in because uh we're going to just look at uh a basic two armed bandit
22:33
problem. [snorts] Uh so yeah this is the for the actual
22:40
algorithm that we're using uh we're going to use this reinforce algorithm which is the foundation of all policy
22:47
gradient uh learning al algorithms is this reinforce algorithm because usually when you how reinforcement learning is
22:54
introduced is is with this like Q-learning uh which is not you're not optimizing the the the strategy itself
23:01
you're saying the optimizing the value fun anyway That's maybe a bit out of scope. So, basically what we're going to
23:07
look at is where we're gonna the first thing we're going to do is look at a partially observable stationary two
23:14
armed bandit. Okay, what the hell does that mean? So, basically we're saying that it's a two- armed bandit.
23:20
Essentially, it's a coin toss, right? Uh, and you know, you can either pick heads
23:27
or tails. And this is a two- armed bandit because there's two choices, right? Can pick heads or tails. We don't
23:32
know what the distribution. And this is a stationary biased coin. So this coin is biased. So it's not 50/50 but and by
23:40
default here it's like 70% probability of going heads. We don't know the underlying distribution. We can only uh
23:48
estimate by playing this game. [snorts] Okay. And also this is the the policy.
23:54
So the policy is is that you pass in some state and it gives you an action. Uh and the action here essentially it's
24:01
the it's the strategy. Uh and it gives you an action like what should you do? Should you go heads or should you go
24:06
tails, right? Uh and that's the so that that's our first uh
24:15
environment and that's is this like stationary bias coin. Uh so what we're
24:20
going to do is we're we we initial we set the the to make this deterministic.
24:26
We set some seeds. We've got our policy which is essentially the the the strategy of like uh choosing our actions
24:33
based on the the state. Uh this is actually stateless. So just put put that out there. So this is like a dummy
24:40
input. Uh we do like a forward pass. So we basically sample an action from the current policy strategy. Uh and we then
24:50
interact with the environment. Okay. If we take this action like what's the
24:55
reward? And the reward is like if it's heads, if you if you guess correctly,
25:01
then you get uh a dollar and if you lose, then you lose $1, right? We're
25:07
just going to keep it like as a static reward because uh it just uh minimizes
25:12
the noise, right? Uh and then we do this the the reinforcement uh reinforce
25:17
algorithm which is basically uh we take the negation of the log probability multiplied by the reward and that's our
25:24
loss function. And then what we do is we just do run the optimization. Uh but we
25:31
it's imperative that we zero out the gradient because if we don't the gradients get accumulated but anyway
25:38
don't worry too much about the the the details here and then after a certain amount of time steps then we just log
25:44
the the current rewards. Uh but and this is the the experiment here and I'm just
25:50
uh show you like for example the the for this we've set it to 70% and we run over
25:56
like 2,000 episodes and let's see what what is the the strategy or the policy
26:01
it's guessed. So you can see here's the rewards over time. You can see it's like
26:06
positive. It never has like negative rewards. Uh what's uh interesting is is
26:13
that you can see here that's the you can see like the policy it has like
26:19
a it believes like uh the heads with a just over 60% probability of going heads
26:27
and this is I should also mention this is a stochastic strategy right so it's sampling from a distribution and it's
26:34
but it's changing here to say like okay it's 100% that it should be go in heads
26:40
here and you can see like it goes like okay it's uh just over 60% to to predict
26:47
heads but as as it's learning it's this policy grained learning it's converging
26:53
to say like okay it should just always go up and that's the optimal is just always bet up right because 70% of the
26:59
time it goes heads so that's the uh um for a stationary bander right but that's
27:07
just a toy example right And now we just add a bit more complexity and just a bit more of a real world real world
27:13
scenario. Right. So now what we're going to do is look at uh partially observable
27:18
non-stationary two armed bandits. And we're just going to simplify things here. We could maybe use like a cyclic s
27:26
function to you know to to cycle between uh different uh
27:33
probabilities right but we're just going to keep it basic here. I'm just saying like after a certain amount of time it's
27:39
going to switch. So before the switch it the probability of heads is going to be
27:44
70%. Then after the switch after 1,000 episodes by default it's
27:51
then going to be a 20 20% probability. So the distribution is going to change over time. Right? [snorts]
27:58
And obviously we can't observe this. We can only partially observe it by playing the game and fully understand it. So,
28:05
for example, when you're doing like uh interviews and they're asking you like maybe run some market making, this this
28:10
is what essentially what you're doing. You're trying to work out what's the distribution of of the the data like uh
28:16
um set prices based on on that distribution. Uh it's similar, right? Um
28:24
okay, so that's our non-stationary bias coin. Ah, and here's a very important
28:29
part is that we need to have some form of regularization. So uh a very key
28:35
important concept uh in reinforcement learning is exploration versus
28:40
exploitation. You can't for example if you just did exploitation the whole time
28:46
[snorts] you would end up in a local optima. And you always want to make sure you never go into like a local optima.
28:53
So it's imagine like you're in a maze, right? uh you could go down a route which is maybe the the shortest path so
29:00
far but it could you know like the long term is that it's a dead end right uh uh
29:06
so you need to to to constantly explore different uh options and you know to to
29:12
to ensure that it doesn't go into a local optim local optima we use this
29:17
what's called entropy uh so this is what's called Shannon
29:22
entropy and as even if you don't understand the mass it doesn't we can build intuition here
29:30
what what what it's uh doing. So for example on a coin toss
29:35
the the the high the max uncertainty is when the probability of heads is 50/50
29:41
right and you know that's intuitive because uh and then the you know the entropy of it is 1.0 zero. But however,
29:49
if it's biased and it's biased like it's just heads 0% of the time, that means
29:54
it's 100% tails, then the entropy is zero. So
30:00
essentially what this entropy regularization is doing is is ensuring that uh you you don't always just sample
30:08
heads all the time or just sample tails all all the the time that you also uh
30:14
because when the distribution changes you may see that okay you actually you you go heads you get reward but over
30:21
time anyway it might be better if I just show you the example right so for example this is our it's just pretty much the the same we just change the
30:28
environment uh [snorts] and we add the entropy loss. So now the
30:35
loss is just uh two terms which is the policy loss and the entropy. So we calculate the entropy of the
30:40
distribution so far the empirical distribution. Uh and you know it's
30:46
exactly the same but we're just calculating the entropy and then we got this entropy beta which is just a
30:52
waiting of the entropy. So we can make it less sensitive to entropy or more sensitive to entropy. And then it's just
30:59
the summation of the policy loss and the entropy loss, right? Uh and again just
31:04
remember because with machine learning it's about minimizing. So we because we
31:10
just take the we just negate it, right? So uh again with the entropy beta we
31:16
just take the the negation of the of the the weight and again we do the machine
31:22
learning. It's exactly the same. Okay. And we're going to run two experiments.
31:29
One with the vanilla uh reinforce which has no entropy regularization. And then
31:35
we're going to want run same again but with entropy regularization
31:40
and you're going to see something very interesting here. Okay. So this coin remember this coin uh bandit changes. Uh
31:49
so just again just imagine you're at the casino. We're we're either choosing one hand or the other. We notice like, okay,
31:55
this hand is giving us money, the other one's not. So, we just choose the left arm, right? But after a certain amount of time, the dodgy casino changes time
32:03
like changes and flip it. Right? If our if we can see here what's happening with
32:08
our vanilla without the entropy regularization, it's making money. But soon as the distribution changes,
32:15
there's a regime change, it's it loses money. And uh we can see what happens on
32:22
the in in this diagram here on the right. So you can see with the vanilla it it's got into a local optima which is
32:29
uh to to go heads which is the optimal for the for the left before the regime
32:34
change. But when there's a reg uh just make it very clear this black line is
32:40
when the regime change regime change happens. So that the the distribution
32:45
change. So this is when the the probability of heads is 70% and this is when then it switches and then it comes
32:51
to 20%. And you can see here that it just always stays at 1%. So it does no
32:57
exploration here. It's just pure exploitation. It found this local optima. It's gotten to it and there's no
33:03
regularization. So it just stays there. So when the actual distribution of the returns or so the you know the bandit
33:10
changes uh it doesn't adapt. Uh but you can see here with the entropy
33:15
regalization it it's never going to like 1% uh it
33:20
sort of does here but as soon as the distribution changes and it's done the regime change you can see it has adapted
33:28
here so it goes all the way back so it was predicting uh heads but soon as the
33:34
change it notice there's a change in the distribution of the of its rewards so
33:40
the the policy has changed to to predict uh heads, [snorts] sorry, tails.
33:49
And you can see like it does it here, right? Uh so you can see this is adaptive and you can even by changing
33:55
the the the beta uh the entropy beta that we can make this even like more quickly adapt even more. Uh so and again
34:04
this is like it's a way more complicated. So I can't just do this all in one video. it needs
34:10
a a dedicated video by itself, but I just wanted to show just some of the principles of like how to handle uh
34:17
ratium changes in uh using reinforcement learning. Okay, so that's the the end of the
34:24
video. So uh just to conclude, so we've like mathematically defined what is a regime change which is the when exhibits
34:30
like non-stationary dynamics in in a financial time or any time series. uh
34:36
we've shown some avenues here to make your machine learning models adaptive. So for example, if you're doing supervised learning that you can encode
34:43
like hidden states uh and this makes it more your supervised learning more
34:49
adaptive. Uh we've also looked at online learning which is actually quite similar to reinforcement learning but there's
34:54
some key fundamental differences. Uh using this passive aggressive learning so it it penalizes it's like a form of
35:02
like online error correction. So it adjusts the weights. If it makes if the if the errors uh uh the predictions are
35:09
wrong, it adjusts the weights. And so this allows us to to to adapt to
35:16
any changes in the distribution of the the returns. Uh and then we also looked
35:22
at this this policy gradient reinforcement learning and that was just a quick look. And there's actually
35:28
another key fundamental difference as well with the online learning. It's just it doesn't consider the cumulative
35:34
returns, right? So it doesn't make a decision now that will give us a better future return like let's say long-term
35:41
return. It's just always like looking okay what's the best return like now and here and now. Uh whereas with
35:48
reinforcement learning learning you can make some I don't know maybe short-term bad decisions but more long-term it's
35:56
much better. So imagine like again like a maze. You could easily if you just you
36:02
could easily go into like a local optima. Uh but then you know there better to
36:08
it's not the most optimal right and again with like trading like if you had like free actions like to to buy uh or
36:16
go long short or just hold or essentially do nothing, right? Uh it could be that you know by holding that
36:23
you you make more returns, right? [snorts] So but yeah we'll look into this in more detail later but then we just looked at
36:30
uh the key thing here is that we looked at the entropy regularization. So this allows us to balance that it doesn't get
36:36
into a local optima and it's a form of uh keeping it uh uh not uh getting in a
36:43
local optima to of exploitation that it looks uh for any changes in the
36:49
distribution of of the the data right okay so I think that's concludes
36:55
everything so I hope that was useful uh please like subscribe and uh also give
37:01
me your comments as well be very interesting to to read them. Okay, thank you very much. Cheers.