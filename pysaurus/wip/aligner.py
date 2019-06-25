from io import StringIO


def identity(value):
    return value


class Alignment:

    __slots__ = ('sequence_1', 'sequence_2', 'difference', 'score')

    def __init__(self, sequence_1, sequence_2, difference, score):
        self.sequence_1 = sequence_1
        self.sequence_2 = sequence_2
        self.difference = difference
        self.score = score

    def to_string(self, separator=None):
        out = StringIO()
        print('[score=%d]' % self.score, file=out)
        print(self.sequence_1 if separator is None else separator.join(str(val) for val in self.sequence_1), file=out)
        print(self.sequence_2 if separator is None else separator.join(str(val) for val in self.sequence_2), file=out)
        print(self.difference if separator is None else separator.join(self.difference), file=out)
        s = out.getvalue()
        out.close()
        return s

    def __str__(self):
        return self.to_string()

    def unique_difference(self):
        len_diff = len(self.difference)
        a = 0
        while a < len_diff:
            if self.difference[a] != 'X':
                break
            a += 1
        b = a + 1
        while b < len_diff:
            if self.difference[b] == 'X':
                break
            b += 1
        c = b + 1
        while c < len_diff:
            if self.difference[c] != 'X':
                break
            c += 1
        if c < len_diff:
            return None
        sub_diff = self.difference[a:b]
        sub_a = self.sequence_1[a:b]
        sub_b = self.sequence_2[a:b]
        return sub_a, sub_b, sub_diff

    def strip_similarities(self):
        acc_a = ''
        acc_b = ''
        acc_diff = ''
        previous = 0
        len_diff = len(self.difference)
        while previous < len_diff:
            a = previous
            while a < len_diff and self.difference[a] == 'X':
                a += 1
            b = a + 1
            while b < len_diff and self.difference[b] != 'X':
                b += 1
            if a - previous > 0:
                acc_a += '|'
                acc_b += '|'
                acc_diff += '|'
            if b - a > 0:
                acc_a += self.sequence_1[a:b]
                acc_b += self.sequence_2[a:b]
                acc_diff += self.difference[a:b]
            previous = b
        return (acc_a, acc_b, acc_diff) if acc_a else None


class Aligner:

    __slots__ = ('match_score', 'diff_score', 'gap_score', 'gap_symbol')

    def __init__(self, match=1, mis_match=-1, in_del=-1, gap=' '):
        self.match_score = match
        self.diff_score = mis_match
        self.gap_score = in_del
        self.gap_symbol = gap

    def align(self, sequence_1, sequence_2, debug=False, score_only=False, matrix=None):
        # sequence_1 in first column
        # sequence_2 in first line
        matrix_width = 1 + len(sequence_2)
        matrix_height = 1 + len(sequence_1)

        if matrix is None:
            matrix = [[i * self.gap_score for i in range(matrix_width)]]
            for i in range(1, matrix_height):
                matrix.append([0] * matrix_width)
        else:
            assert len(matrix) == matrix_height and len(matrix[0]) == matrix_width

        for i in range(1, matrix_height):
            matrix[i][0] = i * self.gap_score
            for j in range(1, matrix_width):
                matrix[i][j] = max(
                    matrix[i - 1][j - 1] + (self.match_score if sequence_1[i - 1] == sequence_2[j - 1]
                                            else self.diff_score),
                    matrix[i - 1][j] + self.gap_score,
                    matrix[i][j - 1] + self.gap_score
                )

        score = matrix[-1][-1]
        if score_only:
            return score

        seq_1 = [self.gap_symbol]
        seq_2 = [self.gap_symbol]
        seq_1.extend(sequence_1)
        seq_2.extend(sequence_2)
        alignment_1 = []
        alignment_2 = []
        alignment_diff = []
        i = matrix_height - 1
        j = matrix_width - 1
        while i > 0 or j > 0:
            if i > 0 and matrix[i][j] == matrix[i - 1][j] + self.gap_score:
                alignment_1.append(seq_1[i])
                alignment_2.append(self.gap_symbol)
                alignment_diff.append('-')
                i -= 1
            elif j > 0 and matrix[i][j] == matrix[i][j - 1] + self.gap_score:
                alignment_1.append(self.gap_symbol)
                alignment_2.append(seq_2[j])
                alignment_diff.append('-')
                j -= 1
            elif (i > 0
                  and j > 0
                  and matrix[i][j] == matrix[i - 1][j - 1] + (
                          self.match_score if seq_1[i] == seq_2[j] else self.diff_score)):
                alignment_1.append(seq_1[i])
                alignment_2.append(seq_2[j])
                alignment_diff.append('X' if seq_1[i] == seq_2[j] else '*')
                i -= 1
                j -= 1
        if debug:
            for row in matrix:
                if row:
                    print(row[0], end='')
                    for i in range(1, len(row)):
                        print('\t%s' % row[i], end='')
                print()
        alignment_1.reverse()
        alignment_2.reverse()
        alignment_diff.reverse()
        return Alignment(alignment_1, alignment_2, alignment_diff, score)
