# The demo of the helper function module which detects bad sensors in our IoT devices

## Issue:
The accurate positioning of sludge height in the circular reservoir of the wastewater treatment plant is crucial for the plant's operation. Traditional methods require periodic manual visual measurements. The Sludge Positioning App we have developed utilizes 16 sensors installed on underwater equipment to cross-locate the floating sludge's height in the wastewater reservoir. 
However, issues such as moisture often lead to sensor damage, and if even one sensor malfunctions, it results in the failure of sludge positioning. This compromises the reliability of the product and incurs high maintenance costs.

## Solution: 
I spent approximately one week observing the data patterns when sensors were damaged. In the second week, I designed a recursive algorithm to pinpoint the malfunctioning sensors. The third week was dedicated to simulating laboratory data, and in the fourth week, I implemented the helper module -- psTrackers. As a result the helper successfully detected bad sensors and ejected bad data as well which led to reducing maintenance intervals from every 2 months to 10 months and improving the overall system stability by 65%.

## Details: 
* The two-dimensional sensor data have time on the vertical axis and real-time photosensitive data from 16 sensors of a specific instrument on the horizontal axis.
* Our psTrackers class employs two filters.
	* The first filter is similar to a Bloom filter, which preliminarily screens problematic sensors based on the historical data variance and monotonicity of a particular sensor.
 	* The second filter assesses the lateral data from the 16 sensors using fuzzy monotonicity judgments. Given the characteristics of sludge and water, at a specific point in time, the data from the 16 sensors of the same instrument should exhibit fuzzy monotonicity. We use a recursive filter called L2RMoving to assess fuzzy monotonicity from left to right.

		
