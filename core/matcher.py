class Matcher:

    def __init__(self):
        pass

    def accumulate(self, reply, answer):
        pass

    def score(self) -> float:
        return 0


class AvgIoUMatcher(Matcher):
    NAME = "avg_iou"

    def __init__(self):
        super(AvgIoUMatcher).__init__()
        self.accumulator = 0.0
        self.accumulated_weight = 0.0

    def accumulate(self, reply, answer, weight: float = 1.0):
        reply = set(reply)
        answer = set(answer)
        intersection_size = len(answer.intersection(reply))
        union_size = len(answer.union(reply))

        if union_size == 0:
            score = 1.0
        else:
            score = float(intersection_size) / float(union_size)

        self.accumulator += score
        self.accumulated_weight += weight

        return score

    def score(self) -> float:
        if self.accumulated_weight > 0.0:
            return self.accumulator / self.accumulated_weight
        return 0.0


MATCHER_MAP = {
    AvgIoUMatcher.NAME: AvgIoUMatcher,
}

def matcher_from_name(name: str):
    return MATCHER_MAP[name]()