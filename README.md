# orhelper
orhelper is a module which aims to facilitate interacting and scripting with OpenRocket from Python.

## Prerequisites
- OpenRocket (tested with version 23.09)
- Java JDK 17. Possible sources include:
     - [Open JDK 17](https://jdk.java.net/archive/#:~:text=17.0.2%20\(build%2017.0.2%2B8\))
     - [Oracle JDK 17](https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html)
     - Ubuntu: `sudo apt-get install openjdk-17-jre`
     - macOS (using [Homebrew](https://brew.sh/)): `brew install openjdk@17`
- Python >= 3.6

## Setup JDK

### Linux
For most people jpype will be able to automatically find the JDK. However, if it fails or you want to be sure you are using the correct version, add the JDK path to a JAVA_HOME environment variable:
- Locate your JDK installation directory (e.g. `/usr/lib/jvm/[YOUR JDK 17 FOLDER HERE]`)
- Open the `~/.bashrc` file with your favorite text editor (will likely need sudo privileges)
- Add the following line to the `~/.bashrc` file:
    ```bash
    export JAVA_HOME="/usr/lib/jvm/[YOUR JDK 17 FOLDER HERE]"
    ```
- Restart your terminal or run the following for the changes to take effect:
    ```bash
    source ~/.bashrc
    ```

### Windows

- Set Windows environment variables to the following:
    - Oracle
        ```bash
        JAVA_HOME = C:\Program Files\Java\[YOUR JDK 17 FOLDER HERE]
        ```
    - OpenJDK
        ```bash
        JAVA_HOME = C:\Program Files\OpenJDK\[YOUR JDK 17 FOLDER HERE]
        ```

### macOS

On macOS, JPype should be able to find the JDK automatically in most cases. If it doesn't, or if you want to ensure you're using a specific JDK version (JDK 17 in this case), you can set the JAVA_HOME environment variable manually to the path of your JDK installation:

1. Open the Terminal application.
2. Locate your JDK 17 installation directory. This is usually `/Library/Java/JavaVirtualMachines/[YOUR JDK 17 FOLDER HERE]/Contents/Home`. You can verify the path by running `/usr/libexec/java_home -v 17` in Terminal, which should output the correct path to JDK 17 if it's installed.
3. Set the JAVA_HOME environment variable by adding the following line to your shell profile file (`~/.bash_profile` for Bash or `~/.zshrc` for Zsh, depending on your shell):

    ```bash
    export JAVA_HOME='/Library/Java/JavaVirtualMachines/[YOUR JDK 17 FOLDER HERE]/Contents/Home'
    ```
4. Apply the changes by running `source ~/.bash_profile` or `source ~/.zshrc`, depending on which file you edited.
5. Verify the JAVA_HOME variable is set correctly by running `echo $JAVA_HOME` in Terminal. It should display the path to JDK 17.

This ensures that orhelper and other Java-dependent applications use the correct version of Java (JDK 17) on your macOS system.

## Installing

- Install orhelper from pip
    ```bash
    pip install orhelper
    ```

- [Download](https://openrocket.info/downloads.html?vers=latest#content-JAR) the OpenRocket.jar file (if you don't already have it)
    - Linux  
        Change `<RELEASE>` to the OpenRocket version number you'd like to download, e.g. `23.09`
        ```bash
        wget https://github.com/openrocket/openrocket/releases/download/release-<RELEASE>/OpenRocket-<RELEASE>.jar
        ```

- Set environment variable `CLASSPATH` path to OpenRocket.jar file. (Only required if it's not already at `.\OpenRocket.jar`)
    ```
    CLASSPATH=\some\path\to\OpenRocket.jar
    ```

- See `examples/` for usage examples
- See [the OpenRocket wiki](https://github.com/openrocket/openrocket/wiki/Scripting-with-Python-and-JPype) for more info on usage and the examples 


## Credits
- Richard Graham for the original script: [Source](https://sourceforge.net/p/openrocket/mailman/openrocket-devel/thread/4F17AA0C.1040002@rdg.cc/)
- @not7cd for some initial organization and clean-up: [Source](https://github.com/not7cd/orhelper)
- And of course everyone who has contributed to OpenRocket over the years.