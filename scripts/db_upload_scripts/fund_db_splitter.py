import os
import time
import chardet

class LargeFile:
    def __init__(self, filePath):
        self.filePath = filePath

    def _detect_encoding(self):
        """
        Detects the encoding of the file for proper reading.
        """
        with open(self.filePath, 'rb') as f:
            result = chardet.detect(f.read(10000))  # Detect based on a portion of the file
            return result['encoding']

    def _extract_sql_file(self):
        """
        Generator function to extract SQL INSERT statements from the file.
        Yields each INSERT statement found in the file.
        """
        encoding = self._detect_encoding()
        with open(self.filePath, 'r', encoding=encoding) as sqlfile:
            buffer = ''
            for line in sqlfile:
                buffer += line
                if line.rstrip().endswith(';'):  # Detect end of a full SQL statement
                    yield buffer.strip()
                    buffer = ''  # Reset buffer for the next statement

    def split_insert_statements(self, folderPath, batch_size=5000):
        """
        Splits the INSERT statements into multiple files, each containing up to batch_size statements.

        Args:
            folderPath (str): The path to the folder where split files will be saved.
            batch_size (int): Maximum number of INSERT statements per file.
        """
        os.makedirs(folderPath, exist_ok=True)  # Ensure output folder exists
        file_count = 1
        insert_count = 0
        current_batch = []

        # Iterate over each SQL segment extracted
        for segment in self._extract_sql_file():
            if segment.startswith('INSERT INTO'):
                current_batch.append(segment)
                insert_count += 1

                # Once batch size is reached, write to a new file
                if insert_count >= batch_size:
                    output_file = os.path.join(folderPath, f"insert_batch_{file_count}.sql")
                    with open(output_file, 'w', encoding='utf-8') as batch_file:
                        batch_file.write('\n\n'.join(current_batch))
                    print(f"Created {output_file} with {insert_count} INSERT statements.")
                    
                    # Prepare for the next batch
                    file_count += 1
                    insert_count = 0
                    current_batch = []

        # Write any remaining INSERT statements that didn't reach batch_size
        if current_batch:
            output_file = os.path.join(folderPath, f"insert_batch_{file_count}.sql")
            with open(output_file, 'w', encoding='utf-8') as batch_file:
                batch_file.write('\n\n'.join(current_batch))
            print(f"Created final {output_file} with {insert_count} INSERT statements.")

# Usage example
filePath = 'fund_data.sql'
outputFolder = 'output_sql_files'
large_file = LargeFile(filePath)

start_time = time.time()
large_file.split_insert_statements(outputFolder)
end_time = time.time()

print(f"Time taken: {end_time - start_time} seconds")
