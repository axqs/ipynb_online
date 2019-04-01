from nbconvert.exporters.latex import LatexExporter
from nbconvert.exporters.pdf import PDFExporter


def latex_max_image_size(source):
  bla = source.replace(r"\includegraphics",
                     r"\adjustimage{max size={0.9\linewidth}{0.9\paperheight}}")
  return bla


def nice_breaks(line, size):
  words = line.split(" ")
  current_string = ""
  for word in words:
      if len(word) > size:
          # word to long, can't do anything
          if len(current_string):
              yield current_string
          yield word
          continue
      if len(word) + len(current_string) + 1 <= size:
          current_string = current_string + " " + word
      else:
          yield current_string
          current_string = word
  yield current_string


def break_lines(text):
  width = 95
  lines = []
  for line in text.split("\n"):
      if len(line) > width:
          lines.extend(list(nice_breaks(line, width)))
      else:
          lines.append(line)
  return "\n".join(lines)


class NiceLatexExporter(LatexExporter):
  def from_notebook_node(self, nb, resources=None, **kw):
      self.register_filter('latex_max_image_size', latex_max_image_size)
      self.register_filter('break_lines', break_lines)
      return super(NiceLatexExporter, self).from_notebook_node(nb, resources, **kw)


class NicePDFExporter(PDFExporter, NiceLatexExporter):
  # diamonds make baby andy cry
  pass