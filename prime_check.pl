#!/usr/bin/perl
use strict;
use warnings;
my $num = shift || 17;
sub is_prime {
    my $n = shift;
    if ($n <= 1) {
        return 0;
    }
    if ($n == 2) {
        return 1;
    }
    if ($n % 2 == 0) {
        return 0;
    }
    my $limit = int(sqrt($n));
    for (my $i = 3; $i <= $limit; $i += 2) {
        if ($n % $i == 0) {
            return 0;
        }
    }
    return 1;
}
if (is_prime($num)) {
    print "Custom message for validation\n";
} else {
    print "$num is not a prime number.\n";
}

