from random import choice

motds = """
Open-source!
%
Distribute!
%
Reverse-engineered!
%
Don't look directly at the features!
%
The work of MAD!
%
Made in the USA!
%
Celestial!
%
Asynchronous!
%
Seasons!
%
Sponges!
%
Simplex noise!
%
MIT-licensed!
%
Unit-tested!
%
Documented!
%
Password login!
%
Fluid simulations!
%
Whoo, Bukkit!
%
Whoo, Charged Miners!
%
Whoo, Mineflayer!
%
Whoo, Mineserver!
%
Whoo, craftd!
%
Can't be held by Bukkit!
%
The test that stumped them all!
%
Comfortably numb!
%
The hidden riddle!
%
We are all made of stars!
%
Out of beta and releasing on time!
%
Still alive!
%
"Pentasyllabic" is an autonym!
"""

motds = [i.strip() for i in motds.split("%")]

def get_motd():
    """
    Retrieve a random MOTD.
    """

    return choice(motds)
