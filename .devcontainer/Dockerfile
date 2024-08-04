# Use a smaller base image
FROM python:3.11.4-slim-bullseye

# Set the working directory in the container
WORKDIR /ArtificialThought

# Copy all the files to the container
COPY . .

# Install the Python dependencies
RUN pip install -r requirements.txt

# Set the default command for the container
CMD ["Bash"]