import matplotlib.pyplot as plt
from morseg.algorithms.tokenizer import PairEncoding
from morseg.utils.wrappers import WordlistWrapper
from pathlib import Path


raw_data_dir = Path(__file__).parent.parent / "raw" / "done"
mandarin = WordlistWrapper.from_file(raw_data_dir / "mand1415.tsv")
hindi = WordlistWrapper.from_file(raw_data_dir / "hind1269.tsv")

model = PairEncoding()
model.train(mandarin, threshold=0, iterations=100000, callbacks=["alphabet_size"])
mandarin_vocab_size = model.training_history["alphabet_size"]

model = PairEncoding()
model.train(hindi, threshold=0, iterations=100000, callbacks=["alphabet_size"])
hindi_vocab_size = model.training_history["alphabet_size"]

plt.plot(mandarin_vocab_size, label="Mandarin")
plt.plot(hindi_vocab_size[:len(mandarin_vocab_size)], label="Hindi")

plt.xlabel("Iterations")
plt.ylabel("Vocabulary Size")
plt.legend()

plt.savefig(Path(__file__).parent / "bpe-vocab-size.pdf")
