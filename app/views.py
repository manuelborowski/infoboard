from flask_table import Col
#Special column to add html-tags.  Note : this can be dangerous, so whatch out!!!
class NoEscapeCol(Col):
    def td_format(self, content):
        return content

