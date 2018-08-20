<map version="1.0.1">
<!-- To view this file, download free mind mapping software FreeMind from http://freemind.sourceforge.net -->
<node CREATED="1534622893270" ID="ID_1774542579" MODIFIED="1534922862984" TEXT="Interface Pysaurus">
<node CREATED="1534623025795" ID="ID_1354623243" MODIFIED="1534922926293" POSITION="right" TEXT="Database DBNAME on disk: folder DBNAME">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1534623025797" ID="ID_1841337615" MODIFIED="1534623025797" TEXT="Folders list file DBNAME.txt"/>
<node CREATED="1534623025798" ID="ID_306560388" MODIFIED="1534922948238" TEXT="JSON database file DBNAME.json">
<node CREATED="1534623025799" ID="ID_476457109" MODIFIED="1534623025799" TEXT="videos: array of videos"/>
<node CREATED="1534623025800" ID="ID_1340761862" MODIFIED="1534623025800" TEXT="tags: array of tags"/>
<node CREATED="1534623025800" ID="ID_83120055" MODIFIED="1534623025800" TEXT="user_queries: array of user-defined queries"/>
</node>
<node CREATED="1534623025801" ID="ID_307803858" MODIFIED="1534623025801" TEXT="Thumbnails *.png"/>
</node>
<node CREATED="1534623025801" FOLDED="true" ID="ID_1952012581" MODIFIED="1534922861625" POSITION="right" TEXT="Tags">
<node CREATED="1534623025803" FOLDED="true" ID="ID_139244904" MODIFIED="1534922860836" TEXT="D&#xe9;finition">
<node CREATED="1534623025803" ID="ID_1269565652" MODIFIED="1534623025803" TEXT="Name: string"/>
<node CREATED="1534623025803" ID="ID_60459494" MODIFIED="1534623025803" TEXT="Dimension: one | many"/>
<node CREATED="1534623025804" ID="ID_1680434040" MODIFIED="1534623025804" TEXT="Type: bool | int | unsigned | float | string"/>
<node CREATED="1534623025804" FOLDED="true" ID="ID_1936568656" MODIFIED="1534922858403" TEXT="Values: null | [allowed values]">
<node CREATED="1534623025804" MODIFIED="1534623025804" TEXT="If empty, any value is accapted."/>
</node>
<node CREATED="1534623025805" FOLDED="true" ID="ID_710597862" MODIFIED="1534922859312" TEXT="default null | value">
<node CREATED="1534623025805" MODIFIED="1534623025805" TEXT="If dimension is one, value must be null or one value"/>
<node CREATED="1534623025806" MODIFIED="1534623025806" TEXT="If dimension is many, value must be null or a list of values"/>
</node>
</node>
<node CREATED="1534623025806" FOLDED="true" ID="ID_420536038" MODIFIED="1534623038321" TEXT="Default tags">
<node CREATED="1534623025807" MODIFIED="1534623025807" TEXT="Category (many string null null)"/>
</node>
<node CREATED="1534623025807" FOLDED="true" ID="ID_1719945459" MODIFIED="1534623038321" TEXT="Special tags">
<node CREATED="1534623025807" MODIFIED="1534623025807" TEXT="Note (one unsigned [(0, 1, 2, 3, 4, 5] 0)"/>
</node>
</node>
<node CREATED="1534623025808" FOLDED="true" ID="ID_1183984032" MODIFIED="1534623038322" POSITION="right" TEXT="Page Welcome">
<node CREATED="1534623025808" MODIFIED="1534623025808" TEXT="Button create a new database -&gt; page **Create database**"/>
<node CREATED="1534623025809" FOLDED="true" ID="ID_1007721685" MODIFIED="1534623038321" TEXT="Button open an existing database">
<node CREATED="1534623025809" MODIFIED="1534623025809" TEXT="Open a folder dialog to select existing database folder"/>
<node CREATED="1534623025809" MODIFIED="1534623025809" TEXT="If database folder is invalid (no list file), display an alert"/>
<node CREATED="1534623025810" MODIFIED="1534623025810" TEXT="Else -&gt; page **Open database**"/>
</node>
</node>
<node CREATED="1534623025810" FOLDED="true" ID="ID_205451424" MODIFIED="1534623038322" POSITION="right" TEXT="Page Create database">
<node CREATED="1534623025810" MODIFIED="1534623025810" TEXT="Button back -&gt; page **Welcome**"/>
<node CREATED="1534623025811" MODIFIED="1534623025811" TEXT="Input database name"/>
<node CREATED="1534623025811" MODIFIED="1534623025811" TEXT="**FolderList** (empty)"/>
<node CREATED="1534623025811" FOLDED="true" ID="ID_1170693287" MODIFIED="1534623038322" TEXT="Button create database">
<node CREATED="1534623025811" FOLDED="true" ID="ID_1937512810" MODIFIED="1534623038322" TEXT="Create database structure on disk. If an error occurs:">
<node CREATED="1534623025812" MODIFIED="1534623025812" TEXT="try to delete database structure, collect any new errors during deletion"/>
<node CREATED="1534623025812" MODIFIED="1534623025812" TEXT="display errors with an alert"/>
</node>
<node CREATED="1534623025813" MODIFIED="1534623025813" TEXT="Else: **load_database()**"/>
</node>
</node>
<node CREATED="1534623025813" FOLDED="true" ID="ID_972883903" MODIFIED="1534623038322" POSITION="right" TEXT="Page Open database">
<node CREATED="1534623025813" MODIFIED="1534623025813" TEXT="Button back -&gt; page **Welcome**"/>
<node CREATED="1534623025814" MODIFIED="1534623025814" TEXT="Label database name"/>
<node CREATED="1534623025814" MODIFIED="1534623025814" TEXT="**FolderList** (filled with folder of loaded database)"/>
<node CREATED="1534623025815" MODIFIED="1534623025815" TEXT="Button load database -&gt; **load_database()**"/>
</node>
<node CREATED="1534623025815" FOLDED="true" ID="ID_1670466380" MODIFIED="1534626435525" POSITION="right" TEXT="Page Database">
<node CREATED="1534623025815" MODIFIED="1534623025815" TEXT="Page title: database name"/>
<node CREATED="1534623025816" FOLDED="true" ID="ID_1463474116" MODIFIED="1534626434654" TEXT="Menu bar">
<node CREATED="1534623025816" FOLDED="true" ID="ID_1583861574" MODIFIED="1534626433903" TEXT="Menu Database">
<node CREATED="1534623025817" MODIFIED="1534623025817" TEXT="Action Refresh database now: -&gt; **load_database()**"/>
<node CREATED="1534623025817" MODIFIED="1534623025817" TEXT="Action **Save database now**"/>
<node CREATED="1534623025817" MODIFIED="1534623025817" TEXT="Action **Close database**"/>
<node CREATED="1534623025818" MODIFIED="1534623025818" TEXT="Action **Delete database completely**"/>
</node>
<node CREATED="1534623025819" FOLDED="true" ID="ID_1094461647" MODIFIED="1534626433098" TEXT="Menu database">
<node CREATED="1534623025820" MODIFIED="1534623025820" TEXT="Action **Manage tags** -&gt; ..."/>
<node CREATED="1534623025820" MODIFIED="1534623025820" TEXT="Action **Manage tag values** (remove/merge some tag values) -&gt; ..."/>
<node CREATED="1534623025820" MODIFIED="1534623025820" TEXT="Action **Manage folders** (add/remove folders from database) -&gt; ..."/>
<node CREATED="1534623025821" FOLDED="true" ID="ID_766448689" MODIFIED="1534623038322" TEXT="Menu Display videos with:">
<node CREATED="1534623025821" MODIFIED="1534623025821" TEXT="Action a same property ... -&gt; **classify for a property**"/>
<node CREATED="1534623025821" MODIFIED="1534623025821" TEXT="Action a same tag ... -&gt; **classify for a tag**"/>
<node CREATED="1534623025822" MODIFIED="1534623025822" TEXT="Action **same properties** -&gt; ..."/>
<node CREATED="1534623025822" MODIFIED="1534623025822" TEXT="Action **same tags** -&gt; ..."/>
<node CREATED="1534623025822" MODIFIED="1534623025822" TEXT="Action **same properties and tags** -&gt; ..."/>
<node CREATED="1534623025823" MODIFIED="1534623025823" TEXT="Action same specific properties and tags ... -&gt; **classify for selected properties and tags**"/>
<node CREATED="1534623025823" MODIFIED="1534623025823" TEXT="Action **same name** (shortcut)"/>
<node CREATED="1534623025823" MODIFIED="1534623025823" TEXT="Action **same size** (shortcut)"/>
<node CREATED="1534623025823" MODIFIED="1534623025823" TEXT="Action **same duration** (shortcut)"/>
</node>
<node CREATED="1534623025824" MODIFIED="1534623025824" TEXT="Action **Display potential similar videos**"/>
<node CREATED="1534623025824" MODIFIED="1534623025824" TEXT="..."/>
</node>
</node>
<node CREATED="1534623025824" FOLDED="true" ID="ID_1966089050" MODIFIED="1534623038323" TEXT="Search bar">
<node CREATED="1534623025825" MODIFIED="1534623025825" TEXT="Input search"/>
<node CREATED="1534623025825" FOLDED="true" ID="ID_581746728" MODIFIED="1534623038323" TEXT="Radio buttons:">
<node CREATED="1534623025825" MODIFIED="1534623025825" TEXT="exact expression"/>
<node CREATED="1534623025826" MODIFIED="1534623025826" TEXT="any word"/>
<node CREATED="1534623025826" MODIFIED="1534623025826" TEXT="all words (default)"/>
</node>
<node CREATED="1534623025826" MODIFIED="1534623025826" TEXT="Option case sensitive (default insensitive)"/>
<node CREATED="1534623025827" MODIFIED="1534623025827" TEXT="Button search ..."/>
<node CREATED="1534623025827" MODIFIED="1534623025827" TEXT="Button advanced search ..."/>
</node>
<node CREATED="1534623025827" FOLDED="true" ID="ID_1002285952" MODIFIED="1534623038324" TEXT="Tab errors (if errors)">
<node CREATED="1534623025827" FOLDED="true" ID="ID_680180461" MODIFIED="1534623038323" TEXT="errors report">
<node CREATED="1534623025828" MODIFIED="1534623025828" TEXT="Display a report about errors occured while loading database or videos,"/>
<node CREATED="1534623025829" MODIFIED="1534623025829" TEXT="from oldest (top) to newest errors."/>
</node>
<node CREATED="1534623025829" FOLDED="true" ID="ID_241485787" MODIFIED="1534623038323" TEXT="Button clear:">
<node CREATED="1534623025829" MODIFIED="1534623025829" TEXT="clear errors report"/>
</node>
</node>
<node CREATED="1534623025830" FOLDED="true" ID="ID_454468225" MODIFIED="1534623038325" TEXT="Tab display: display videos for a selection">
<node CREATED="1534623025830" FOLDED="true" ID="ID_1175016008" MODIFIED="1534623038324" TEXT="display title bar">
<node CREATED="1534623025831" MODIFIED="1534623025831" TEXT="Label display description"/>
<node CREATED="1534623025832" MODIFIED="1534623025832" TEXT="Button manage display columns ..."/>
</node>
<node CREATED="1534623025832" MODIFIED="1534623025832" TEXT="list of videos for current diplay."/>
<node CREATED="1534623025832" FOLDED="true" ID="ID_263670070" MODIFIED="1534623038325" TEXT="View for currently selected video(s).">
<node CREATED="1534623025833" FOLDED="true" ID="ID_701467861" MODIFIED="1534623038324" TEXT="(if 0 videos selected): informations about videos of current selection">
<node CREATED="1534623025833" MODIFIED="1534623025833" TEXT="Label number of folders"/>
<node CREATED="1534623025834" MODIFIED="1534623025834" TEXT="Label number of files"/>
<node CREATED="1534623025834" MODIFIED="1534623025834" TEXT="Label total size"/>
<node CREATED="1534623025834" MODIFIED="1534623025834" TEXT="Label total duration"/>
</node>
<node CREATED="1534623025835" FOLDED="true" ID="ID_1238103161" MODIFIED="1534623038324" TEXT="(if 1 video selected)">
<node CREATED="1534623025835" MODIFIED="1534623025835" TEXT="Button open video"/>
<node CREATED="1534623025835" MODIFIED="1534623025835" TEXT="Button delete video from disk"/>
<node CREATED="1534623025836" MODIFIED="1534623025836" TEXT="Label filename"/>
<node CREATED="1534623025836" MODIFIED="1534623025836" TEXT="Label title"/>
<node CREATED="1534623025836" MODIFIED="1534623025836" TEXT="Label $size, $container ($videoCodec, $audioCodec)"/>
<node CREATED="1534623025837" MODIFIED="1534623025837" TEXT="Label $width X $height, $frameRate / sec"/>
<node CREATED="1534623025837" MODIFIED="1534623025837" TEXT="Label $duration, $sampleRate Hz, $bitrate / sec"/>
<node CREATED="1534623025837" FOLDED="true" ID="ID_1161375743" MODIFIED="1534623038324" TEXT="Section tags">
<node CREATED="1534623025838" MODIFIED="1534623025838" TEXT="button add a tag ..."/>
<node CREATED="1534623025838" FOLDED="true" ID="ID_1101039214" MODIFIED="1534623038324" TEXT="for each defined tag:">
<node CREATED="1534623025839" MODIFIED="1534623025839" TEXT="tag name, tag values"/>
<node CREATED="1534623025839" MODIFIED="1534623025839" TEXT="button modify ..."/>
<node CREATED="1534623025839" MODIFIED="1534623025839" TEXT="button delete ..."/>
</node>
</node>
<node CREATED="1534623025840" MODIFIED="1534623025840" TEXT="(if wwarnings) list of warnings"/>
<node CREATED="1534623025840" MODIFIED="1534623025840" TEXT="diaplay thumbnail"/>
</node>
<node CREATED="1534623025840" FOLDED="true" ID="ID_1751692831" MODIFIED="1534623038325" TEXT="(if many videos selected)">
<node CREATED="1534623025841" MODIFIED="1534623025841" TEXT="Label number of selected videos"/>
<node CREATED="1534623025841" MODIFIED="1534623025841" TEXT="Label total size"/>
<node CREATED="1534623025841" MODIFIED="1534623025841" TEXT="Label containers"/>
<node CREATED="1534623025842" MODIFIED="1534623025842" TEXT="Label video codecs"/>
<node CREATED="1534623025842" MODIFIED="1534623025842" TEXT="Label audio codecs"/>
<node CREATED="1534623025842" MODIFIED="1534623025842" TEXT="Label total duration, min duration, max duration"/>
<node CREATED="1534623025843" MODIFIED="1534623025843" TEXT="Label min width, max width"/>
<node CREATED="1534623025843" MODIFIED="1534623025843" TEXT="Label min height, max height"/>
<node CREATED="1534623025843" MODIFIED="1534623025843" TEXT="Label min framerate, max framerate"/>
<node CREATED="1534623025844" MODIFIED="1534623025844" TEXT="Label min samplerate, max samplerate"/>
<node CREATED="1534623025844" MODIFIED="1534623025844" TEXT="Label min bitrate, max bitrate"/>
<node CREATED="1534623025844" FOLDED="true" ID="ID_344801323" MODIFIED="1534623038325" TEXT="Section tag">
<node CREATED="1534623025844" MODIFIED="1534623025844" TEXT="Button add common tag ..."/>
<node CREATED="1534623025845" FOLDED="true" ID="ID_352729671" MODIFIED="1534623038324" TEXT="For each tag present in any selected video:">
<node CREATED="1534623025845" MODIFIED="1534623025845" TEXT="tag name, all tags values in selected videos"/>
<node CREATED="1534623025845" MODIFIED="1534623025845" TEXT="button modify ..."/>
<node CREATED="1534623025846" MODIFIED="1534623025846" TEXT="button delete ..."/>
</node>
</node>
</node>
</node>
</node>
<node CREATED="1534623025846" FOLDED="true" ID="ID_61311938" MODIFIED="1534623038325" TEXT="Status bas:">
<node CREATED="1534623025846" MODIFIED="1534623025846" TEXT="Label database name"/>
<node CREATED="1534623025847" MODIFIED="1534623025847" TEXT="Label number of folders"/>
<node CREATED="1534623025847" MODIFIED="1534623025847" TEXT="Label number of files"/>
<node CREATED="1534623025847" MODIFIED="1534623025847" TEXT="Label total size in highest unit (To, Go, Mo or Ko)"/>
<node CREATED="1534623025848" MODIFIED="1534623025848" TEXT="Label total diration (hours + minutes + secondes + microseconds)"/>
<node CREATED="1534623025848" MODIFIED="1534623025848" TEXT="Label latest saved time"/>
</node>
</node>
<node CREATED="1534623025849" FOLDED="true" ID="ID_385703235" MODIFIED="1534623038326" POSITION="right" TEXT="FolderList">
<node CREATED="1534623025849" FOLDED="true" ID="ID_810164964" MODIFIED="1534623038325" TEXT="entries. For each entry:">
<node CREATED="1534623025849" MODIFIED="1534623025849" TEXT="Button remove: remove entry from list"/>
</node>
<node CREATED="1534623025850" FOLDED="true" ID="ID_1608139133" MODIFIED="1534623038325" TEXT="Button add new:">
<node CREATED="1534623025850" MODIFIED="1534623025850" TEXT="Open a folder dialog to select an existing videos directory"/>
<node CREATED="1534623025851" MODIFIED="1534623025851" TEXT="Display an alert if selected path is not a valid existing folder"/>
<node CREATED="1534623025851" MODIFIED="1534623025851" TEXT="Else, add folder to list database_folders"/>
</node>
</node>
<node CREATED="1534623025852" FOLDED="true" ID="ID_1800280013" MODIFIED="1534623038326" POSITION="right" TEXT="Function load_database():">
<node CREATED="1534623025852" FOLDED="true" ID="ID_814569524" MODIFIED="1534623038326" TEXT="(see current database loading code)">
<node CREATED="1534623025853" MODIFIED="1534623025853" TEXT="collect all potential errors"/>
</node>
<node CREATED="1534623025853" MODIFIED="1534623025853" TEXT="-&gt; page **Database** (with errors collected)"/>
</node>
<node CREATED="1534623025853" FOLDED="true" ID="ID_71931542" MODIFIED="1534623038326" POSITION="right" TEXT="Action Save database now:">
<node CREATED="1534623025854" MODIFIED="1534623025854" TEXT="Save database"/>
<node CREATED="1534623025855" MODIFIED="1534623025855" TEXT="Collect potential errors and write them into errors report"/>
<node CREATED="1534623025855" MODIFIED="1534623025855" TEXT="If errors occured, display errors report"/>
</node>
<node CREATED="1534623025855" FOLDED="true" ID="ID_333403749" MODIFIED="1534623038326" POSITION="right" TEXT="Action Close database:">
<node CREATED="1534623025855" MODIFIED="1534623025855" TEXT="Dialog to confirm"/>
<node CREATED="1534623025856" MODIFIED="1534623025856" TEXT="If confirmed:"/>
<node CREATED="1534623025856" FOLDED="true" ID="ID_993673472" MODIFIED="1534623038326" TEXT="Save database:">
<node CREATED="1534623025856" FOLDED="true" ID="ID_308688128" MODIFIED="1534623038326" TEXT="If errors occured while saving:">
<node CREATED="1534623025857" MODIFIED="1534623025857" TEXT="Write errors in errors report"/>
<node CREATED="1534623025857" MODIFIED="1534623025857" TEXT="Ask user if he still wants to close database"/>
<node CREATED="1534623025857" FOLDED="true" ID="ID_860491523" MODIFIED="1534623038326" TEXT="If user confirms:">
<node CREATED="1534623025858" MODIFIED="1534623025858" TEXT="Unload database from memory"/>
<node CREATED="1534623025858" MODIFIED="1534623025858" TEXT="-&gt; page **Welcome**"/>
</node>
</node>
<node CREATED="1534623025859" FOLDED="true" ID="ID_652617558" MODIFIED="1534623038326" TEXT="Else">
<node CREATED="1534623025859" MODIFIED="1534623025859" TEXT="Unload database from memory"/>
<node CREATED="1534623025859" MODIFIED="1534623025859" TEXT="-&gt; Page **Welcome**"/>
</node>
</node>
<node CREATED="1534623025860" MODIFIED="1534623025860" TEXT="Unload database from memory"/>
</node>
<node CREATED="1534623025860" FOLDED="true" ID="ID_554566892" MODIFIED="1534623038327" POSITION="right" TEXT="Action Delete database completely:">
<node CREATED="1534623025861" MODIFIED="1534623025861" TEXT="Dialog to confirm"/>
<node CREATED="1534623025861" FOLDED="true" ID="ID_1541971308" MODIFIED="1534623038327" TEXT="If confirmed:">
<node CREATED="1534623025861" MODIFIED="1534623025861" TEXT="Unload database from memory (do not save it)"/>
<node CREATED="1534623025862" FOLDED="true" ID="ID_610256070" MODIFIED="1534623038327" TEXT="Delete database from disk">
<node CREATED="1534623025863" MODIFIED="1534623025863" TEXT="If errors occur, display a dialog box, and tell user he can manually"/>
<node CREATED="1534623025863" MODIFIED="1534623025863" TEXT="delete database folder to remove database"/>
</node>
<node CREATED="1534623025864" MODIFIED="1534623025864" TEXT="-&gt; page **Welcome**"/>
</node>
</node>
<node CREATED="1534623025864" FOLDED="true" ID="ID_777448635" MODIFIED="1534623038327" POSITION="right" TEXT="Feature Manage tags">
<node CREATED="1534623025864" MODIFIED="1534623025864" TEXT="Button **Add new tag** -&gt; ..."/>
<node CREATED="1534623025865" FOLDED="true" ID="ID_1761972668" MODIFIED="1534623038327" TEXT="List of tags. For each tag:">
<node CREATED="1534623025865" MODIFIED="1534623025865" TEXT="Labels: tag name, tag dimension, tag type, tag values, tag default value"/>
<node CREATED="1534623025866" FOLDED="true" ID="ID_1781449404" MODIFIED="1534623038327" TEXT="Button remove:">
<node CREATED="1534623025867" FOLDED="true" ID="ID_300181511" MODIFIED="1534623038327" TEXT="Dialog to confirm. If confirmed:">
<node CREATED="1534623025868" MODIFIED="1534623025868" TEXT="Delete tag values from database"/>
<node CREATED="1534623025868" MODIFIED="1534623025868" TEXT="Delete tag from databse"/>
<node CREATED="1534623025869" MODIFIED="1534623025869" TEXT="Delete tag from this list"/>
</node>
</node>
<node CREATED="1534623025869" MODIFIED="1534623025869" TEXT="Button modify -&gt; feature **Modify tag**"/>
</node>
</node>
<node CREATED="1534623025870" FOLDED="true" ID="ID_1712298211" MODIFIED="1534623038328" POSITION="right" TEXT="Feature Manage tag values">
<node CREATED="1534623025871" MODIFIED="1534623025871" TEXT="Select tag to manage"/>
<node CREATED="1534623025872" FOLDED="true" ID="ID_166901393" MODIFIED="1534623038328" TEXT="Sort bar">
<node CREATED="1534623025872" MODIFIED="1534623025872" TEXT="(if tag type is string) Checkbox sort values by string length"/>
<node CREATED="1534623025873" FOLDED="true" ID="ID_490682258" MODIFIED="1534623038328" TEXT="Select sort direction:">
<node CREATED="1534623025874" MODIFIED="1534623025874" TEXT="ascending"/>
<node CREATED="1534623025874" MODIFIED="1534623025874" TEXT="descending"/>
</node>
</node>
<node CREATED="1534623025874" FOLDED="true" ID="ID_1719612142" MODIFIED="1534623038328" TEXT="List of values for selected tag. For each value:">
<node CREATED="1534623025875" MODIFIED="1534623025875" TEXT="Checkbox to select it"/>
<node CREATED="1534623025875" MODIFIED="1534623025875" TEXT="Label value"/>
<node CREATED="1534623025875" MODIFIED="1534623025875" TEXT="Label to telle if it&apos;s a current default value"/>
<node CREATED="1534623025876" MODIFIED="1534623025876" TEXT="Label number of videos with this value"/>
<node CREATED="1534623025876" FOLDED="true" ID="ID_1574852191" MODIFIED="1534623038328" TEXT="Button rename:">
<node CREATED="1534623025876" FOLDED="true" ID="ID_551464984" MODIFIED="1534623038328" TEXT="Dialog box:">
<node CREATED="1534623025877" MODIFIED="1534623025877" TEXT="Label tag name"/>
<node CREATED="1534623025877" MODIFIED="1534623025877" TEXT="Label current value to rename"/>
<node CREATED="1534623025878" MODIFIED="1534623025878" TEXT="Input new name"/>
<node CREATED="1534623025878" MODIFIED="1534623025878" TEXT="Button cancel: close dialog"/>
<node CREATED="1534623025879" FOLDED="true" ID="ID_152883838" MODIFIED="1534623038328" TEXT="Button rename:">
<node CREATED="1534623025879" MODIFIED="1534623025879" TEXT="Change current value name with new given name everywhere current value appears in videos"/>
<node CREATED="1534623025880" MODIFIED="1534623025880" TEXT="Close dialog"/>
</node>
</node>
</node>
</node>
<node CREATED="1534623025880" FOLDED="true" ID="ID_1157537067" MODIFIED="1534623038328" TEXT="Button delete selected values:">
<node CREATED="1534623025880" MODIFIED="1534623025880" TEXT="Dialog to confirm"/>
<node CREATED="1534623025881" MODIFIED="1534623025881" TEXT="If confirmed, delete selected values from database and from list"/>
</node>
</node>
<node CREATED="1534623025881" FOLDED="true" ID="ID_570394512" MODIFIED="1534623038330" POSITION="right" TEXT="Feature Add new tag">
<node CREATED="1534623025881" MODIFIED="1534623025881" TEXT="Input tag name"/>
<node CREATED="1534623025882" MODIFIED="1534623025882" TEXT="Radio buttons: tag dimensions: one, many"/>
<node CREATED="1534623025882" MODIFIED="1534623025882" TEXT="Radio buttons: tag type: bool, int, unsigned, float, string"/>
<node CREATED="1534623025883" FOLDED="true" ID="ID_992037959" MODIFIED="1534623038329" TEXT="Section allowed values (leave empty to allow any value)">
<node CREATED="1534623025884" FOLDED="true" ID="ID_1938937246" MODIFIED="1534623038328" TEXT="List of allowed values. For each value:">
<node CREATED="1534623025884" MODIFIED="1534623025884" TEXT="Button remove: remove value from list"/>
<node CREATED="1534623025885" MODIFIED="1534623025885" TEXT="(if dimension is one) radio button: default value: set as default value"/>
<node CREATED="1534623025886" MODIFIED="1534623025886" TEXT="(if dimension is many) checkbox: default value: add to default values"/>
</node>
<node CREATED="1534623025887" FOLDED="true" ID="ID_1143808258" MODIFIED="1534623038328" TEXT="Form add an allowed value">
<node CREATED="1534623025887" MODIFIED="1534623025887" TEXT="Input value"/>
<node CREATED="1534623025888" MODIFIED="1534623025888" TEXT="Button add: add value to list of allowed values"/>
</node>
</node>
<node CREATED="1534623025889" FOLDED="true" ID="ID_1024046210" MODIFIED="1534623038329" TEXT="(if no allowed values)">
<node CREATED="1534623025889" MODIFIED="1534623025889" TEXT="(if dimension is one) Input default value (optional)"/>
<node CREATED="1534623025889" FOLDED="true" ID="ID_15155641" MODIFIED="1534623038329" TEXT="(if dimension is many) List of default values">
<node CREATED="1534623025890" FOLDED="true" ID="ID_688847314" MODIFIED="1534623038329" TEXT="Default values list. For each value:">
<node CREATED="1534623025890" MODIFIED="1534623025890" TEXT="Button remove: remove value from list"/>
</node>
<node CREATED="1534623025891" MODIFIED="1534623025891" TEXT="Input new default value + button add: add value to list"/>
</node>
</node>
<node CREATED="1534623025891" MODIFIED="1534623025891" TEXT="Button cancel: close feature"/>
<node CREATED="1534623025891" FOLDED="true" ID="ID_803073130" MODIFIED="1534623038329" TEXT="Button add:">
<node CREATED="1534623025892" MODIFIED="1534623025892" TEXT="If tag settings are invalid, alert"/>
<node CREATED="1534623025892" MODIFIED="1534623025892" TEXT="Else, add tag to database"/>
</node>
</node>
<node CREATED="1534623025892" FOLDED="true" ID="ID_1376090418" MODIFIED="1534623038333" POSITION="right" TEXT="Feature Modify tag">
<node CREATED="1534623025893" FOLDED="true" ID="ID_1640830831" MODIFIED="1534623038330" TEXT="Bar">
<node CREATED="1534623025893" MODIFIED="1534623025893" TEXT="Label &quot;Name: {current name}&quot;"/>
<node CREATED="1534623025893" MODIFIED="1534623025893" TEXT="Input tag name (default: current tag name)"/>
</node>
<node CREATED="1534623025894" FOLDED="true" ID="ID_1135500701" MODIFIED="1534623038330" TEXT="Bar">
<node CREATED="1534623025894" MODIFIED="1534623025894" TEXT="Label &quot;Dimension: {current dimension}&quot;"/>
<node CREATED="1534623025895" MODIFIED="1534623025895" TEXT="Select [one, many] (default: current tag dimension)"/>
</node>
<node CREATED="1534623025896" FOLDED="true" ID="ID_393570048" MODIFIED="1534623038330" TEXT="Section &quot;Allowed values: {current allowed values separated by commas, or all}&quot;">
<node CREATED="1534623025896" FOLDED="true" ID="ID_1356544009" MODIFIED="1534623038330" TEXT="List of allowed values. For each value:">
<node CREATED="1534623025897" MODIFIED="1534623025897" TEXT="Button remove: remove value from list"/>
<node CREATED="1534623025897" MODIFIED="1534623025897" TEXT="(if dimension is one) radio button: default value: set as default value"/>
<node CREATED="1534623025897" MODIFIED="1534623025897" TEXT="(if dimension is many) checkbox: default value: add to default values"/>
</node>
<node CREATED="1534623025898" FOLDED="true" ID="ID_1631631807" MODIFIED="1534623038330" TEXT="Form Add an allowed value">
<node CREATED="1534623025898" MODIFIED="1534623025898" TEXT="Input value"/>
<node CREATED="1534623025899" MODIFIED="1534623025899" TEXT="Button add: add value to list of allowed values"/>
</node>
</node>
<node CREATED="1534623025899" FOLDED="true" ID="ID_967691224" MODIFIED="1534623038331" TEXT="(if no allowed values)">
<node CREATED="1534623025899" FOLDED="true" ID="ID_761669257" MODIFIED="1534623038330" TEXT="(if dimension is one) Bar">
<node CREATED="1534623025900" MODIFIED="1534623025900" TEXT="Label &quot;default value: {current default value, or none}&quot;"/>
<node CREATED="1534623025900" MODIFIED="1534623025900" TEXT="Input default value (default: current tag default value)"/>
</node>
<node CREATED="1534623025900" FOLDED="true" ID="ID_1889228770" MODIFIED="1534623038330" TEXT="(if dimension is many) Section &quot;default values: {current default values, or none}&quot;">
<node CREATED="1534623025901" FOLDED="true" ID="ID_92591226" MODIFIED="1534623038330" TEXT="List of default values. For each value:">
<node CREATED="1534623025901" MODIFIED="1534623025901" TEXT="Button remove: remove value from list"/>
</node>
<node CREATED="1534623025901" MODIFIED="1534623025901" TEXT="Input new default value + button add: add value to list"/>
</node>
</node>
<node CREATED="1534623025902" MODIFIED="1534623025902" TEXT="Select &quot;current type: {current type}&quot; (default: current tag type)"/>
<node CREATED="1534623025902" MODIFIED="1534623025902" TEXT="(if new type requires a default value for conversion) Input &quot;Replace unconvertible old values with:&quot;"/>
<node CREATED="1534623025902" MODIFIED="1534623025902" TEXT="Button cancel: close feature"/>
<node CREATED="1534623025903" MODIFIED="1534623025903" TEXT="Button reset: reload feature will current tag properties"/>
<node CREATED="1534623025903" FOLDED="true" ID="ID_1060255890" MODIFIED="1534623038333" TEXT="Button update:">
<node CREATED="1534623025903" FOLDED="true" ID="ID_1939165538" MODIFIED="1534623038331" TEXT="name">
<node CREATED="1534623025904" FOLDED="true" ID="ID_437737654" MODIFIED="1534623038331" TEXT="If new name matchs existing tag name:">
<node CREATED="1534623025904" FOLDED="true" ID="ID_1085616380" MODIFIED="1534623038331" TEXT="Either both tags must have exactly same other properties (dimension, allowed values, default values, type)">
<node CREATED="1534623025905" MODIFIED="1534623025905" TEXT="Ask user to confirm tags will be merged"/>
<node CREATED="1534623025905" MODIFIED="1534623025905" TEXT="If confirmed, merge tags"/>
</node>
<node CREATED="1534623025906" FOLDED="true" ID="ID_309224372" MODIFIED="1534623038331" TEXT="Else, unable to rename:">
<node CREATED="1534623025906" MODIFIED="1534623025906" TEXT="Tell user he must either choose another new name or make sure both tags have exactly same properties before"/>
<node CREATED="1534623025908" MODIFIED="1534623025908" TEXT="merging"/>
</node>
</node>
</node>
<node CREATED="1534623025908" FOLDED="true" ID="ID_1784867263" MODIFIED="1534623038331" TEXT="dimension">
<node CREATED="1534623025909" MODIFIED="1534623025909" TEXT="many -&gt; one: tag must have only 1 value per video where he appears, otherwise unable to change dimension"/>
</node>
<node CREATED="1534623025910" FOLDED="true" ID="ID_1342436809" MODIFIED="1534623038332" TEXT="allowed values">
<node CREATED="1534623025910" FOLDED="true" ID="ID_243813081" MODIFIED="1534623038331" TEXT="null -&gt; allowed values">
<node CREATED="1534623025911" MODIFIED="1534623025911" TEXT="if some videos have disallowed values based on new given allowed values, ask user if he wants to remove"/>
<node CREATED="1534623025912" MODIFIED="1534623025912" TEXT="disallowed values from videos"/>
<node CREATED="1534623025912" MODIFIED="1534623025912" TEXT="if confirmed, remove disallowed values and update tag"/>
<node CREATED="1534623025913" MODIFIED="1534623025913" TEXT="otherwise, cannot set allowed values"/>
</node>
</node>
<node CREATED="1534623025913" MODIFIED="1534623025913" TEXT="default value"/>
<node CREATED="1534623025913" FOLDED="true" ID="ID_397220621" MODIFIED="1534623038333" TEXT="type">
<node CREATED="1534623025914" FOLDED="true" ID="ID_254059931" MODIFIED="1534623038332" TEXT="bool">
<node CREATED="1534623025914" MODIFIED="1534623025914" TEXT="int, unsigned, float: false -&gt; 0, true -&gt; 1"/>
<node CREATED="1534623025914" MODIFIED="1534623025914" TEXT="string: false -&gt; &quot;0&quot;, true -&gt; &quot;1&quot;"/>
</node>
<node CREATED="1534623025915" FOLDED="true" ID="ID_1759759423" MODIFIED="1534623038332" TEXT="int">
<node CREATED="1534623025915" MODIFIED="1534623025915" TEXT="bool: 0 -&gt; false, else true"/>
<node CREATED="1534623025915" FOLDED="true" ID="ID_1353868989" MODIFIED="1534623038332" TEXT="unsigned:">
<node CREATED="1534623025916" MODIFIED="1534623025916" TEXT="required default_value (= 0) for negative values"/>
<node CREATED="1534623025916" MODIFIED="1534623025916" TEXT="if value &lt; 0, then default_value, else value"/>
</node>
<node CREATED="1534623025916" MODIFIED="1534623025916" TEXT="float: same"/>
<node CREATED="1534623025917" MODIFIED="1534623025917" TEXT="string: string representation"/>
</node>
<node CREATED="1534623025917" FOLDED="true" ID="ID_221751793" MODIFIED="1534623038332" TEXT="unsigned">
<node CREATED="1534623025918" MODIFIED="1534623025918" TEXT="bool: 0 -&gt; false, else true"/>
<node CREATED="1534623025919" MODIFIED="1534623025919" TEXT="int, float: same"/>
<node CREATED="1534623025919" MODIFIED="1534623025919" TEXT="string: string representation"/>
</node>
<node CREATED="1534623025919" FOLDED="true" ID="ID_1899085418" MODIFIED="1534623038332" TEXT="float">
<node CREATED="1534623025919" MODIFIED="1534623025919" TEXT="bool: 0 -&gt; false, else true"/>
<node CREATED="1534623025919" MODIFIED="1534623025919" TEXT="int: int(value) (decimal part is truncated)"/>
<node CREATED="1534623025919" FOLDED="true" ID="ID_1889705518" MODIFIED="1534623038332" TEXT="unsigned:">
<node CREATED="1534623025920" MODIFIED="1534623025920" TEXT="required default_value (= 0) for negative values"/>
<node CREATED="1534623025920" MODIFIED="1534623025920" TEXT="if value &lt; 0, then default_value, else int(value)"/>
</node>
<node CREATED="1534623025920" MODIFIED="1534623025920" TEXT="string: string representation"/>
</node>
<node CREATED="1534623025921" FOLDED="true" ID="ID_259463912" MODIFIED="1534623038332" TEXT="string">
<node CREATED="1534623025921" MODIFIED="1534623025921" TEXT="bool: &quot;&quot; -&gt; false, else true"/>
<node CREATED="1534623025922" FOLDED="true" ID="ID_1968229735" MODIFIED="1534623038332" TEXT="int, unsigned, float:">
<node CREATED="1534623025922" MODIFIED="1534623025922" TEXT="required default_value (= 0) for un-parsable strings"/>
<node CREATED="1534623025923" MODIFIED="1534623025923" TEXT="(for int and unsigned) parse_fn = parseInt"/>
<node CREATED="1534623025923" MODIFIED="1534623025923" TEXT="(for float) parse_fn = parseFloat"/>
<node CREATED="1534623025923" MODIFIED="1534623025923" TEXT="parse_fn(value) or default_value"/>
</node>
</node>
</node>
</node>
</node>
<node CREATED="1534623025923" FOLDED="true" ID="ID_523580948" MODIFIED="1534623038333" POSITION="right" TEXT="Feature Manage folders">
<node CREATED="1534623025924" MODIFIED="1534623025924" TEXT="**FolderList**"/>
<node CREATED="1534623025924" MODIFIED="1534623025924" TEXT="Checkbox refresh database on update"/>
<node CREATED="1534623025924" MODIFIED="1534623025924" TEXT="Button cancel: close feature"/>
<node CREATED="1534623025925" FOLDED="true" ID="ID_1680767555" MODIFIED="1534623038333" TEXT="Button update">
<node CREATED="1534623025925" MODIFIED="1534623025925" TEXT="Update database folders list"/>
<node CREATED="1534623025925" MODIFIED="1534623025925" TEXT="If refresh databse on update: -&gt; **load_database()**"/>
</node>
</node>
<node CREATED="1534623025926" FOLDED="true" ID="ID_351388898" MODIFIED="1534623047591" POSITION="right" TEXT="NB:">
<node CREATED="1534623025926" MODIFIED="1534623025926" TEXT="`a in {x, y, z} &lt;=&gt; a == x OR a == y OR a == Z`"/>
<node CREATED="1534623025927" MODIFIED="1534623025927" TEXT="`a not in {x, y z} &lt;=&gt; a != x AND a != y AND a != z`"/>
</node>
<node CREATED="1534623025928" FOLDED="true" ID="ID_430789714" MODIFIED="1534623038333" POSITION="right" TEXT="DatabaseQueryBuilder">
<node CREATED="1534623025928" FOLDED="true" ID="ID_1931844346" MODIFIED="1534623038333" TEXT="List of query parts. For each part:">
<node CREATED="1534623025928" MODIFIED="1534623025928" TEXT="Button remove: remove part from query"/>
<node CREATED="1534623025929" FOLDED="true" ID="ID_1017300195" MODIFIED="1534623038333" TEXT="Button modify:">
<node CREATED="1534623025930" MODIFIED="1534623025930" TEXT="(if query piece) -&gt; **Query piece** (modify)"/>
<node CREATED="1534623025930" MODIFIED="1534623025930" TEXT="(if query group) -&gt; **Query group** (modify)"/>
</node>
</node>
<node CREATED="1534623025930" MODIFIED="1534623025930" TEXT="Button add a query piece -&gt; **Query piece** (add)"/>
<node CREATED="1534623025931" MODIFIED="1534623025931" TEXT="Button add a query group -&gt; **Query group** (add)"/>
</node>
<node CREATED="1534623025931" FOLDED="true" ID="ID_806115820" MODIFIED="1534623038334" POSITION="right" TEXT="Database Query Group (action=add|modify)">
<node CREATED="1534623025931" MODIFIED="1534623025931" TEXT="Select query group type: AND | OR | XOR"/>
<node CREATED="1534623025932" MODIFIED="1534623025932" TEXT="Section query pieces:"/>
<node CREATED="1534623025932" FOLDED="true" ID="ID_1578221125" MODIFIED="1534623038334" TEXT="List of query pieces. For each piece:">
<node CREATED="1534623025932" MODIFIED="1534623025932" TEXT="Button remove: remove piece from group"/>
<node CREATED="1534623025933" MODIFIED="1534623025933" TEXT="Button modify: -&gt; **Query piece** (modify)"/>
</node>
<node CREATED="1534623025933" MODIFIED="1534623025933" TEXT="Button add a query piece: -&gt; **Query piece** (add)"/>
<node CREATED="1534623025934" FOLDED="true" ID="ID_591708641" MODIFIED="1534623038334" TEXT="Button {action}">
<node CREATED="1534623025934" MODIFIED="1534623025934" TEXT="(if action == add) add query group to given list"/>
<node CREATED="1534623025934" MODIFIED="1534623025934" TEXT="(if add modify) Return modified query group"/>
</node>
</node>
<node CREATED="1534623025934" FOLDED="true" ID="ID_1007636685" MODIFIED="1534623038334" POSITION="right" TEXT="Database Query Piece (action=add|modify)">
<node CREATED="1534623025935" MODIFIED="1534623025935" TEXT="Select tag or property"/>
<node CREATED="1534623025935" MODIFIED="1534623025935" TEXT="Select test type:"/>
<node CREATED="1534623025936" MODIFIED="1534623025936" TEXT="* =="/>
<node CREATED="1534623025936" MODIFIED="1534623025936" TEXT="* !="/>
<node CREATED="1534623025936" MODIFIED="1534623025936" TEXT="* &lt;"/>
<node CREATED="1534623025937" MODIFIED="1534623025937" TEXT="* &lt;="/>
<node CREATED="1534623025937" MODIFIED="1534623025937" TEXT="* \&gt;"/>
<node CREATED="1534623025938" MODIFIED="1534623025938" TEXT="* \&gt;="/>
<node CREATED="1534623025938" MODIFIED="1534623025938" TEXT="* &quot;is defined&quot;"/>
<node CREATED="1534623025938" MODIFIED="1534623025938" TEXT="* &quot;is undefined&quot;"/>
<node CREATED="1534623025939" MODIFIED="1534623025939" TEXT="* (if field type is string) contains exactly"/>
<node CREATED="1534623025939" MODIFIED="1534623025939" TEXT="* (if field type is string) contains any of"/>
<node CREATED="1534623025939" MODIFIED="1534623025939" TEXT="* (if field type is string) contains all of"/>
<node CREATED="1534623025940" MODIFIED="1534623025940" TEXT="* (if field type is string) does not contains exactly"/>
<node CREATED="1534623025940" MODIFIED="1534623025940" TEXT="* (if field type is string) contains none of"/>
<node CREATED="1534623025940" MODIFIED="1534623025940" TEXT="* (if field type is string) does not contains any of"/>
<node CREATED="1534623025941" FOLDED="true" ID="ID_1129775556" MODIFIED="1534623038334" TEXT="Section test values">
<node CREATED="1534623025941" FOLDED="true" ID="ID_1610335167" MODIFIED="1534623038334" TEXT="(if &quot;contains&quot; in test type)">
<node CREATED="1534623025941" MODIFIED="1534623025941" TEXT="Input text to search, words separated with spaces"/>
</node>
<node CREATED="1534623025942" FOLDED="true" ID="ID_1799300165" MODIFIED="1534623038334" TEXT="(else if &quot;defined&quot; not in test type) Bar:">
<node CREATED="1534623025942" MODIFIED="1534623025942" TEXT="Select value to check: {set of all current field values used in videos}"/>
</node>
</node>
<node CREATED="1534623025943" FOLDED="true" ID="ID_555066259" MODIFIED="1534623038334" TEXT="Button {action}:">
<node CREATED="1534623025943" MODIFIED="1534623025943" TEXT="(if action == add) Add query piece to given list"/>
<node CREATED="1534623025944" MODIFIED="1534623025944" TEXT="(if action == modify) Return modified query piece"/>
</node>
</node>
<node CREATED="1534623025944" FOLDED="true" ID="ID_209716142" MODIFIED="1534623038336" POSITION="right" TEXT="Function classify_videos(properties=None, tags=None):">
<node CREATED="1534623025945" FOLDED="true" ID="ID_1891717797" MODIFIED="1534623038335" TEXT="NB: database classifier, keywords:">
<node CREATED="1534623025945" MODIFIED="1534623025945" TEXT="none: None"/>
<node CREATED="1534623025946" MODIFIED="1534623025946" TEXT="all: []"/>
<node CREATED="1534623025946" MODIFIED="1534623025946" TEXT="some: [...]"/>
</node>
<node CREATED="1534623025947" FOLDED="true" ID="ID_1841610572" MODIFIED="1534623038335" TEXT="if properties is None and tags is None:">
<node CREATED="1534623025947" MODIFIED="1534623025947" TEXT="return []"/>
</node>
<node CREATED="1534623025947" FOLDED="true" ID="ID_550716755" MODIFIED="1534623038335" TEXT="if properties is None and tags is []:">
<node CREATED="1534623025948" MODIFIED="1534623025948" TEXT="same values for all tags"/>
</node>
<node CREATED="1534623025948" FOLDED="true" ID="ID_455503255" MODIFIED="1534623038335" TEXT="if properties is None and tags is [...]:">
<node CREATED="1534623025949" MODIFIED="1534623025949" TEXT="same values for given tags"/>
</node>
<node CREATED="1534623025949" FOLDED="true" ID="ID_1424549079" MODIFIED="1534623038335" TEXT="if properties is [] and tags is None:">
<node CREATED="1534623025950" MODIFIED="1534623025950" TEXT="same values for all properties"/>
</node>
<node CREATED="1534623025950" FOLDED="true" ID="ID_1760192515" MODIFIED="1534623038335" TEXT="if properties is [] and tags is []:">
<node CREATED="1534623025951" MODIFIED="1534623025951" TEXT="same values for all properties and tags"/>
</node>
<node CREATED="1534623025951" FOLDED="true" ID="ID_1463646537" MODIFIED="1534623038335" TEXT="if properties is [] and tags is [...]:">
<node CREATED="1534623025951" MODIFIED="1534623025951" TEXT="same values for all properties and given tags"/>
</node>
<node CREATED="1534623025952" FOLDED="true" ID="ID_149717234" MODIFIED="1534623038335" TEXT="if properties is [...] and tags is None:">
<node CREATED="1534623025952" MODIFIED="1534623025952" TEXT="same values for given properties"/>
</node>
<node CREATED="1534623025952" FOLDED="true" ID="ID_1826882900" MODIFIED="1534623038335" TEXT="if properties is [...] and tags is []:">
<node CREATED="1534623025953" MODIFIED="1534623025953" TEXT="same values for given properties and all tags"/>
</node>
<node CREATED="1534623025953" FOLDED="true" ID="ID_1617059068" MODIFIED="1534623038335" TEXT="if properties is [...] and tags is [...]:">
<node CREATED="1534623025953" MODIFIED="1534623025953" TEXT="same values for given properties and tags"/>
</node>
<node CREATED="1534623025954" FOLDED="true" ID="ID_189963429" MODIFIED="1534623038336" TEXT="return classified videos: list of dictionaries, for each dictionary:">
<node CREATED="1534623025954" MODIFIED="1534623025954" TEXT="properties: dictionary mapping a property name to property value common for these videos"/>
<node CREATED="1534623025954" MODIFIED="1534623025954" TEXT="tags: dictionary mapping a tag name to tag value(s) common for these videos"/>
<node CREATED="1534623025955" MODIFIED="1534623025955" TEXT="videos: list of videos"/>
</node>
</node>
<node CREATED="1534623025955" FOLDED="true" ID="ID_427259962" MODIFIED="1534623038336" POSITION="right" TEXT="Function display_classification(params)">
<node CREATED="1534623025955" MODIFIED="1534623025955" TEXT="results = classify_videos(**params)"/>
<node CREATED="1534623025956" MODIFIED="1534623025956" TEXT="Set display with results"/>
</node>
<node CREATED="1534623025956" FOLDED="true" ID="ID_34829898" MODIFIED="1534623038336" POSITION="right" TEXT="Feature classify for a property">
<node CREATED="1534623025956" MODIFIED="1534623025956" TEXT="Select property_name"/>
<node CREATED="1534623025957" MODIFIED="1534623025957" TEXT="Button cancel: close feature"/>
<node CREATED="1534623025957" MODIFIED="1534623025957" TEXT="Button search: -&gt; display_classification(properties=[property_name])"/>
</node>
<node CREATED="1534623025958" FOLDED="true" ID="ID_1931179845" MODIFIED="1534623038336" POSITION="right" TEXT="Feature classify for a tag">
<node CREATED="1534623025959" MODIFIED="1534623025959" TEXT="Select tag_name"/>
<node CREATED="1534623025959" MODIFIED="1534623025959" TEXT="Button cancel: close feature"/>
<node CREATED="1534623025960" MODIFIED="1534623025960" TEXT="Button search: -&gt; display_classification(taga=[tag_name])"/>
</node>
<node CREATED="1534623025960" FOLDED="true" ID="ID_736671930" MODIFIED="1534623038336" POSITION="right" TEXT="Action same properties">
<node CREATED="1534623025960" MODIFIED="1534623025960" TEXT="display_classification(properties=[])"/>
</node>
<node CREATED="1534623025961" FOLDED="true" ID="ID_1859368034" MODIFIED="1534623038336" POSITION="right" TEXT="Action same tags">
<node CREATED="1534623025961" MODIFIED="1534623025961" TEXT="display_classification(tags=[])"/>
</node>
<node CREATED="1534623025961" FOLDED="true" ID="ID_1512724080" MODIFIED="1534623038336" POSITION="right" TEXT="Action same properties and tags">
<node CREATED="1534623025962" MODIFIED="1534623025962" TEXT="display_classification(properties=[], tags=[])"/>
</node>
<node CREATED="1534623025962" FOLDED="true" ID="ID_1439947521" MODIFIED="1534623038337" POSITION="right" TEXT="Feature classify for selected properties and tags:">
<node CREATED="1534623025962" FOLDED="true" ID="ID_1822525235" MODIFIED="1534623038336" TEXT="List of properties. For each property:">
<node CREATED="1534623025963" MODIFIED="1534623025963" TEXT="Checkbox to select it"/>
<node CREATED="1534623025963" MODIFIED="1534623025963" TEXT="Property name"/>
</node>
<node CREATED="1534623025964" FOLDED="true" ID="ID_773218777" MODIFIED="1534623038336" TEXT="List of tag. For each tag:">
<node CREATED="1534623025964" MODIFIED="1534623025964" TEXT="Checkbox to select if"/>
<node CREATED="1534623025965" MODIFIED="1534623025965" TEXT="Tag name"/>
</node>
<node CREATED="1534623025965" MODIFIED="1534623025965" TEXT="Button cancel: close feature"/>
<node CREATED="1534623025965" MODIFIED="1534623025965" TEXT="Button search: display_classification(properties=[selected properties], tags=[selected tags])"/>
</node>
<node CREATED="1534623025966" FOLDED="true" ID="ID_1610672072" MODIFIED="1534623038337" POSITION="right" TEXT="Action same name:">
<node CREATED="1534623025966" MODIFIED="1534623025966" TEXT="display_classification(properties=[title])"/>
</node>
<node CREATED="1534623025967" FOLDED="true" ID="ID_902450726" MODIFIED="1534623038337" POSITION="right" TEXT="Action same size:">
<node CREATED="1534623025967" MODIFIED="1534623025967" TEXT="display_classification(properties=[size])"/>
</node>
<node CREATED="1534623025967" FOLDED="true" ID="ID_843140083" MODIFIED="1534623038337" POSITION="right" TEXT="Action same duration:">
<node CREATED="1534623025968" MODIFIED="1534623025968" TEXT="display_classification(properties=[duration])"/>
</node>
<node CREATED="1534623025968" FOLDED="true" ID="ID_633822253" MODIFIED="1534623038337" POSITION="right" TEXT="Action Display potential similar videos (TODO)">
<node CREATED="1534623025968" MODIFIED="1534623025968" TEXT="results_name = classify_videos(properties=[title])"/>
<node CREATED="1534623025969" MODIFIED="1534623025969" TEXT="results_size = classify_videos(properties=[size])"/>
<node CREATED="1534623025969" MODIFIED="1534623025969" TEXT="results_duration = classify_videos(properties=[duration])"/>
<node CREATED="1534623025969" MODIFIED="1534623025969" TEXT="TODO merge ..."/>
</node>
</node>
</map>
